"""Effect resolution, card actions execution, and state transitions for WHOT-ML (P0-D1, P0-D4)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from whot_ml.action import Action, ActionType
from whot_ml.card import Card, SpecialEffect
from whot_ml.event import Event, EventType
from whot_ml.invariants import InvariantValidator
from whot_ml.rules_engine import RulesEngine
from whot_ml.ruleset import LastCardViolationPenalty
from whot_ml.state import GameState
from whot_ml.turn_manager import TurnManager, TurnModifier


@dataclass(frozen=True)
class StepResult:
    """The structured outcome of an executed action transition."""
    action: Action
    acting_player: int
    events: List[Event]
    rewards: Dict[int, float]
    terminated: bool
    truncated: bool
    next_player: int


class EffectResolver:
    """Resolves card plays, draws, special effects, penalties, market exhaustion, and terminal conditions."""

    @classmethod
    def draw_card(cls, state: GameState, player: int, events: List[Event]) -> Optional[Card]:
        """Draw a single card for a player, invoking market exhaustion reshuffle if necessary.

        Market ordering semantics:
          - Top of market is market[-1] (popped from end).
          - When market is empty, play_pile is preserved up to its top card,
            and remaining cards are shuffled into a new market.
          - Returns the drawn Card or None if market is completely exhausted.
        """
        if not state.market:
            # Market is empty: attempt recycle of discard pile
            if len(state.play_pile) > 1:
                top_card = state.play_pile.pop()
                recyclable = state.play_pile
                state.play_pile = [top_card]
                state.rng_manager.shuffle(recyclable)
                state.market = recyclable

                events.append(
                    Event(
                        event_type=EventType.MARKET_RESHUFFLED,
                        timestep=state.timestep,
                        details={"recycled_count": len(recyclable)},
                    )
                )
            else:
                # Completely exhausted market! No cards to recycle.
                events.append(
                    Event(
                        event_type=EventType.DRAW_UNAVAILABLE,
                        timestep=state.timestep,
                        player=player,
                    )
                )
                return None

        card = state.market.pop()
        state.hands[player].append(card)

        # If player held 1 card and declared, receiving another card invalidates the declaration
        if len(state.hands[player]) != 1:
            state.last_card_declared[player] = False

        # Public event: Player drew a card (card_id hidden from public)
        events.append(
            Event(
                event_type=EventType.CARD_DRAWN,
                timestep=state.timestep,
                player=player,
                card_id=None,
                is_public=True,
            )
        )
        # Private event: Card identity visible only to recipient
        events.append(
            Event(
                event_type=EventType.PRIVATE_CARD_RECEIVED,
                timestep=state.timestep,
                player=player,
                card_id=card.id,
                is_public=False,
            )
        )
        return card

    @classmethod
    def draw_n_cards(cls, state: GameState, player: int, n: int, events: List[Event]) -> List[Card]:
        """Draw up to n cards for a player."""
        drawn: List[Card] = []
        for _ in range(n):
            c = cls.draw_card(state, player, events)
            if c is not None:
                drawn.append(c)
            else:
                break
        return drawn

    @classmethod
    def apply_action(cls, state: GameState, action: Action) -> StepResult:
        """Execute an action following the complete Phase 0 resolution pipeline."""
        acting_player = state.current_player
        events: List[Event] = []

        # Step 1 & 2: Validate action legality
        RulesEngine.validate_action(state, action, acting_player)

        cfg = state.config
        state.timestep += 1
        state.turn_count += 1

        terminated = False
        truncated = False
        rewards: Dict[int, float] = {p: 0.0 for p in range(cfg.player_count)}

        # Case A: Last-Card Declaration
        if action.action_type == ActionType.DECLARE_LAST:
            state.last_card_declared[acting_player] = True
            events.append(
                Event(
                    event_type=EventType.LAST_CARD_DECLARED,
                    timestep=state.timestep,
                    player=acting_player,
                )
            )
            if cfg.declaration_advances_turn:
                next_p, _ = TurnManager.advance_player(
                    current_player=acting_player,
                    num_players=cfg.player_count,
                    direction=state.turn_direction,
                    modifier=TurnModifier.NORMAL,
                )
                state.current_player = next_p
            else:
                # Baseline: declaration does not consume the turn
                next_p = acting_player

        # Case B: DRAW Action
        elif action.action_type == ActionType.DRAW:
            if state.has_active_penalty:
                # Resolving active Pick Two / Pick Three penalty
                penalty_count = state.active_penalty_count
                penalty_type = state.active_penalty_type
                cls.draw_n_cards(state, acting_player, penalty_count, events)

                events.append(
                    Event(
                        event_type=EventType.PENALTY_RESOLVED,
                        timestep=state.timestep,
                        player=acting_player,
                        penalty_count=penalty_count,
                        details={"penalty_type": penalty_type.value if penalty_type else None},
                    )
                )
                state.active_penalty_type = None
                state.active_penalty_count = 0
            else:
                # Normal single card draw
                cls.draw_card(state, acting_player, events)

            # Turn advances normally after drawing
            next_p, _ = TurnManager.advance_player(
                current_player=acting_player,
                num_players=cfg.player_count,
                direction=state.turn_direction,
                modifier=TurnModifier.NORMAL,
            )
            state.current_player = next_p

        # Case C: PLAY or PLAY_WHOT Action
        elif action.action_type in (ActionType.PLAY, ActionType.PLAY_WHOT):
            # 1. Remove card from player hand
            hand = state.hands[acting_player]
            matching_cards = [c for c in hand if c.id == action.card_id]
            if not matching_cards:
                raise ValueError(f"Card {action.card_id} not found in player {acting_player}'s hand")
            card = matching_cards[0]
            hand.remove(card)

            # 2. Add card to play pile
            state.play_pile.append(card)

            # 3. Update active call
            if action.action_type == ActionType.PLAY_WHOT:
                assert action.selected_shape is not None
                state.current_call = action.selected_shape
                events.append(
                    Event(
                        event_type=EventType.CARD_PLAYED,
                        timestep=state.timestep,
                        player=acting_player,
                        card_id=card.id,
                    )
                )
                events.append(
                    Event(
                        event_type=EventType.WHOT_SHAPE_SELECTED,
                        timestep=state.timestep,
                        player=acting_player,
                        shape=action.selected_shape,
                    )
                )
            else:
                state.current_call = card.shape
                events.append(
                    Event(
                        event_type=EventType.CARD_PLAYED,
                        timestep=state.timestep,
                        player=acting_player,
                        card_id=card.id,
                    )
                )

            # 4. Resolve special card effect
            card_effect = cfg.special_card_mapping.get(card.value)

            if card_effect == SpecialEffect.HOLD_ON and cfg.hold_on_enabled:
                state.turn_modifier = TurnModifier.EXTRA_TURN
                events.append(
                    Event(
                        event_type=EventType.HOLD_ON_ACTIVATED,
                        timestep=state.timestep,
                        player=acting_player,
                    )
                )

            elif card_effect == SpecialEffect.PICK_TWO and cfg.pick_two_enabled:
                if state.has_active_penalty and state.active_penalty_type == SpecialEffect.PICK_TWO:
                    events.append(
                        Event(
                            event_type=EventType.PENALTY_STACKED,
                            timestep=state.timestep,
                            player=acting_player,
                            penalty_count=state.active_penalty_count + 2,
                        )
                    )
                else:
                    events.append(
                        Event(
                            event_type=EventType.PENALTY_ACTIVATED,
                            timestep=state.timestep,
                            player=acting_player,
                            penalty_count=2,
                        )
                    )
                state.active_penalty_type = SpecialEffect.PICK_TWO
                state.active_penalty_count += 2

            elif card_effect == SpecialEffect.PICK_THREE and cfg.pick_three_enabled:
                if state.has_active_penalty and state.active_penalty_type == SpecialEffect.PICK_THREE:
                    events.append(
                        Event(
                            event_type=EventType.PENALTY_STACKED,
                            timestep=state.timestep,
                            player=acting_player,
                            penalty_count=state.active_penalty_count + 3,
                        )
                    )
                else:
                    events.append(
                        Event(
                            event_type=EventType.PENALTY_ACTIVATED,
                            timestep=state.timestep,
                            player=acting_player,
                            penalty_count=3,
                        )
                    )
                state.active_penalty_type = SpecialEffect.PICK_THREE
                state.active_penalty_count += 3

            elif card_effect == SpecialEffect.SUSPENSION and cfg.suspension_enabled:
                state.turn_modifier = TurnModifier.SKIP_NEXT
                events.append(
                    Event(
                        event_type=EventType.TURN_SKIPPED,
                        timestep=state.timestep,
                        player=acting_player,
                    )
                )

            elif card_effect == SpecialEffect.GENERAL_MARKET and cfg.general_market_enabled:
                events.append(
                    Event(
                        event_type=EventType.GENERAL_MARKET_ACTIVATED,
                        timestep=state.timestep,
                        player=acting_player,
                    )
                )
                recipients = TurnManager.get_recipients_in_order(
                    current_player=acting_player,
                    num_players=cfg.player_count,
                    direction=state.turn_direction,
                )
                for r in recipients:
                    cls.draw_card(state, r, events)

            # 5. Check Terminal State and Victory
            if len(hand) == 0:
                # Attempting victory! Check declaration requirements
                declared = state.last_card_declared.get(acting_player, False)
                if cfg.last_card_declaration_enabled and not declared:
                    # Undeclared attempted victory violation!
                    events.append(
                        Event(
                            event_type=EventType.LAST_CARD_DECLARATION_VIOLATION,
                            timestep=state.timestep,
                            player=acting_player,
                        )
                    )
                    # Apply configured violation penalty
                    penalty_amount = (
                        1 if cfg.last_card_violation_penalty == LastCardViolationPenalty.DRAW_1 else 2
                    )
                    cls.draw_n_cards(state, acting_player, penalty_amount, events)

                    # Hand is no longer empty, game continues!
                    next_p, _ = TurnManager.advance_player(
                        current_player=acting_player,
                        num_players=cfg.player_count,
                        direction=state.turn_direction,
                        modifier=state.turn_modifier,
                    )
                    state.current_player = next_p
                    state.turn_modifier = TurnModifier.NORMAL
                else:
                    # Valid victory!
                    terminated = True
                    state.is_terminal = True
                    state.winner = acting_player

                    events.append(
                        Event(
                            event_type=EventType.ROUND_ENDED,
                            timestep=state.timestep,
                            player=acting_player,
                        )
                    )
                    events.append(
                        Event(
                            event_type=EventType.GAME_OVER,
                            timestep=state.timestep,
                            player=acting_player,
                        )
                    )

                    for p in range(cfg.player_count):
                        rewards[p] = 1.0 if p == acting_player else -1.0
                    next_p = acting_player
            else:
                # Hand is not empty, advance turn
                next_p, _ = TurnManager.advance_player(
                    current_player=acting_player,
                    num_players=cfg.player_count,
                    direction=state.turn_direction,
                    modifier=state.turn_modifier,
                )
                state.current_player = next_p
                state.turn_modifier = TurnModifier.NORMAL

        # Truncation check
        if state.turn_count >= cfg.maximum_turns and not terminated:
            truncated = True
            state.is_terminal = True

        # Invariant validation in debug mode
        if cfg.debug_mode:
            InvariantValidator.validate(state)

        return StepResult(
            action=action,
            acting_player=acting_player,
            events=events,
            rewards=rewards,
            terminated=terminated,
            truncated=truncated,
            next_player=state.current_player,
        )
