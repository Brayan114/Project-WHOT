"""Rules Engine and Action Masking for WHOT-ML (P0-D1, P0-D2, P0-D4)."""

from __future__ import annotations

from typing import List, Optional

from whot_ml.action import (
    ACTION_INDEX_DECLARE_LAST,
    ACTION_INDEX_DRAW,
    TOTAL_ACTIONS,
    Action,
    ActionType,
    index_to_action,
    make_declare_last_action,
    make_draw_action,
    make_play_card_action,
    make_play_whot_action,
)
from whot_ml.card import Card, CardType, Shape, SpecialEffect
from whot_ml.ruleset import FinalCardOnePolicy, StackingMode, WHOTConfig
from whot_ml.state import GameState


class IllegalActionError(ValueError):
    """Raised when an illegal action is submitted in strict evaluation mode."""
    pass


class RulesEngine:
    """Interprets game rules, validates actions, and generates legal action masks."""

    @classmethod
    def is_card_playable(
        cls,
        card: Card,
        top_card: Card,
        current_call: Shape,
        active_penalty_type: Optional[SpecialEffect],
        active_penalty_count: int,
        hand_size: int,
        config: WHOTConfig,
    ) -> bool:
        """Determine whether a single card is legally playable in the given situation."""
        # 1. Active penalty in effect (P0-D4 Section 18, 19, 21)
        if active_penalty_count > 0 and active_penalty_type is not None:
            if active_penalty_type == SpecialEffect.PICK_TWO:
                if not config.pick_two_enabled:
                    return False
                # Does WHOT defend?
                if card.is_whot:
                    return config.whot_defends_penalty
                # Normal Pick Two defense
                if card.value == 2 and config.special_card_mapping.get(2) == SpecialEffect.PICK_TWO:
                    return True
                # Cross-stacking if configured
                if config.pick_two_stacking == StackingMode.ANY_PICK_CARD:
                    return card.value in (2, 5)
                return False

            elif active_penalty_type == SpecialEffect.PICK_THREE:
                if not config.pick_three_enabled:
                    return False
                if card.is_whot:
                    return config.whot_defends_penalty
                if card.value == 5 and config.special_card_mapping.get(5) == SpecialEffect.PICK_THREE:
                    return True
                if config.pick_three_stacking == StackingMode.ANY_PICK_CARD:
                    return card.value in (2, 5)
                return False

            return False

        # 2. No active penalty: Normal matching (P0-D1 Section 5, P0-D4 Section 13)
        # Check Final Card 1 restriction (P0-D1 Section 8, P0-D4 Section 28)
        if hand_size == 1 and card.value == 1 and config.hold_on_enabled:
            if config.final_card_one_policy == FinalCardOnePolicy.REJECT_LEGALITY:
                return False

        # WHOT card is wild
        if card.is_whot:
            return True

        # Ordinary card matching: same shape OR same number
        return (card.shape == current_call) or (card.value == top_card.value)

    @classmethod
    def legal_actions(cls, state: GameState, player_id: Optional[int] = None) -> List[Action]:
        """Compute the complete list of legal Action objects for the player.

        Rules applied:
          - Only current_player can act; terminal games have no legal actions.
          - DECLARE_LAST is legal if hand_size == 1 and not yet declared.
          - If playable cards exist, DRAW is strictly illegal under WHOT-NG-v1.
          - If no playable card exists, DRAW is the only normal card action.
          - Under active penalties, defense and draw obey penalty_defense_mandatory.
        """
        player = player_id if player_id is not None else state.current_player

        if state.is_terminal:
            return []

        if player != state.current_player:
            return []

        hand = state.player_hand(player)
        hand_size = len(hand)
        cfg = state.config
        legal: List[Action] = []

        # 1. Declaration action (P0-D4 Section 25)
        can_declare = (
            cfg.last_card_declaration_enabled
            and hand_size == 1
            and not state.last_card_declared.get(player, False)
        )
        if can_declare:
            legal.append(make_declare_last_action())

        # 2. Playable card actions
        playable_card_actions: List[Action] = []
        for card in hand:
            if cls.is_card_playable(
                card=card,
                top_card=state.top_card,
                current_call=state.current_call,
                active_penalty_type=state.active_penalty_type,
                active_penalty_count=state.active_penalty_count,
                hand_size=hand_size,
                config=cfg,
            ):
                if card.is_whot:
                    for shape in cfg.whot_shape_selection_options:
                        playable_card_actions.append(make_play_whot_action(card, shape))
                else:
                    playable_card_actions.append(make_play_card_action(card))

        legal.extend(playable_card_actions)

        # 3. DRAW action legality
        if state.has_active_penalty:
            # When facing a penalty:
            if playable_card_actions:
                # Player has at least one valid defense in hand
                if not cfg.penalty_defense_mandatory:
                    # Player may optionally choose to draw the accumulated penalty
                    legal.append(make_draw_action())
            else:
                # Player has no defense: must draw the penalty
                legal.append(make_draw_action())
        else:
            # Normal play:
            # If playable card exists, DRAW is ILLEGAL.
            # If no playable card exists, DRAW is the only card action.
            if not playable_card_actions:
                legal.append(make_draw_action())

        return legal

    @classmethod
    def action_mask(cls, state: GameState, player_id: Optional[int] = None) -> List[int]:
        """Return a 76-element binary mask [0 or 1] indicating legal actions."""
        mask = [0] * TOTAL_ACTIONS
        actions = cls.legal_actions(state, player_id)
        for act in actions:
            mask[act.action_id] = 1
        return mask

    @classmethod
    def is_action_legal(cls, state: GameState, action: Action, player_id: Optional[int] = None) -> bool:
        """Check if a specific Action is currently legal."""
        player = player_id if player_id is not None else state.current_player
        if player != state.current_player or state.is_terminal:
            return False
        legal = cls.legal_actions(state, player)
        return action in legal

    @classmethod
    def validate_action(cls, state: GameState, action: Action, player_id: Optional[int] = None) -> None:
        """Validate an action, raising IllegalActionError if illegal."""
        player = player_id if player_id is not None else state.current_player
        if not cls.is_action_legal(state, action, player):
            raise IllegalActionError(
                f"Action {action} is illegal for player {player} in current state "
                f"(top_card={state.top_card}, call={state.current_call}, "
                f"penalty={state.active_penalty_type} x {state.active_penalty_count})"
            )
