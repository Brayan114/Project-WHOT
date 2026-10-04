"""Player Observation model and information boundary enforcement for WHOT-ML (P0-D2, P0-D4)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from whot_ml.action import TOTAL_ACTIONS, Action, index_to_action
from whot_ml.card import (
    CANONICAL_CARD_BY_ID,
    Card,
    Shape,
    SpecialEffect,
)
from whot_ml.event import Event
from whot_ml.rules_engine import RulesEngine
from whot_ml.ruleset import WHOTConfig
from whot_ml.state import GameState


@dataclass(frozen=True)
class PlayerObservation:
    """The complete and strictly isolated observation available to an individual player.

    Information Boundary Invariants (P0-D2 Section 7, P0-D4 Section 31):
      - Own hand is visible; opponent hands are NEVER exposed.
      - Public play pile and current call are visible.
      - Public hand sizes and market count are visible, but market order and
        card identities in the market are strictly hidden.
      - Public event history is visible; private opponent events are strictly hidden.
      - Simulator RNG state is NEVER exposed.
    """
    player_id: int
    hand: Tuple[Card, ...]
    play_pile: Tuple[Card, ...]
    current_call: Shape
    current_player: int
    active_penalty_type: Optional[SpecialEffect]
    active_penalty_count: int
    hand_sizes: Dict[int, int]
    last_card_declared: Dict[int, bool]
    market_size: int
    public_history: Tuple[Event, ...]
    private_events: Tuple[Event, ...]
    action_mask: Tuple[int, ...]
    ruleset: WHOTConfig
    timestep: int
    turn_count: int
    is_terminal: bool
    winner: Optional[int]

    @property
    def top_card(self) -> Card:
        """The currently visible top card on the play pile."""
        return self.play_pile[-1]

    @property
    def is_my_turn(self) -> bool:
        """Return True if this player is currently the active decision-maker."""
        return self.player_id == self.current_player and not self.is_terminal

    @property
    def legal_actions(self) -> List[Action]:
        """Return the list of legal Action objects available to this player."""
        if not self.is_my_turn:
            return []
        return [index_to_action(idx) for idx, val in enumerate(self.action_mask) if val == 1]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the observation to a JSON-safe dictionary.

        Verifies that no hidden opponent cards or market identities are included.
        """
        return {
            "player_id": self.player_id,
            "hand": [c.id for c in self.hand],
            "play_pile": [c.id for c in self.play_pile],
            "current_call": self.current_call.value,
            "current_player": self.current_player,
            "active_penalty_type": (
                self.active_penalty_type.value if self.active_penalty_type else None
            ),
            "active_penalty_count": self.active_penalty_count,
            "hand_sizes": {str(k): v for k, v in self.hand_sizes.items()},
            "last_card_declared": {str(k): v for k, v in self.last_card_declared.items()},
            "market_size": self.market_size,
            "public_history": [e.to_dict() for e in self.public_history],
            "private_events": [e.to_dict() for e in self.private_events],
            "action_mask": list(self.action_mask),
            "ruleset": self.ruleset.to_dict(),
            "timestep": self.timestep,
            "turn_count": self.turn_count,
            "is_terminal": self.is_terminal,
            "winner": self.winner,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PlayerObservation:
        """Reconstruct PlayerObservation from serialized dictionary."""
        d = dict(data)
        hand = tuple(CANONICAL_CARD_BY_ID[cid] for cid in d["hand"])
        play_pile = tuple(CANONICAL_CARD_BY_ID[cid] for cid in d["play_pile"])
        current_call = Shape(d["current_call"])
        penalty_type = (
            SpecialEffect(d["active_penalty_type"])
            if d.get("active_penalty_type")
            else None
        )
        hand_sizes = {int(k): v for k, v in d["hand_sizes"].items()}
        last_card_declared = {int(k): v for k, v in d["last_card_declared"].items()}
        public_history = tuple(Event.from_dict(e) for e in d["public_history"])
        private_events = tuple(Event.from_dict(e) for e in d["private_events"])
        action_mask = tuple(d["action_mask"])
        ruleset = WHOTConfig.from_dict(d["ruleset"])

        return cls(
            player_id=d["player_id"],
            hand=hand,
            play_pile=play_pile,
            current_call=current_call,
            current_player=d["current_player"],
            active_penalty_type=penalty_type,
            active_penalty_count=d["active_penalty_count"],
            hand_sizes=hand_sizes,
            last_card_declared=last_card_declared,
            market_size=d["market_size"],
            public_history=public_history,
            private_events=private_events,
            action_mask=action_mask,
            ruleset=ruleset,
            timestep=d["timestep"],
            turn_count=d["turn_count"],
            is_terminal=d["is_terminal"],
            winner=d["winner"],
        )


class ObservationGenerator:
    """Dedicated factory for constructing PlayerObservation from GameState."""

    @classmethod
    def generate(
        cls,
        state: GameState,
        player_id: int,
        history: Optional[List[Event]] = None,
    ) -> PlayerObservation:
        """Generate a strictly filtered PlayerObservation for the given player.

        Architecturally prevents accidental leakage of opponent hands, market order,
        or RNG state.
        """
        if not (0 <= player_id < state.config.player_count):
            raise ValueError(f"Player {player_id} out of range for {state.config.player_count} players")

        # 1. Own hand (tuple of immutable Card references)
        own_hand = tuple(state.hands[player_id])

        # 2. Public play pile (immutable tuple)
        public_play_pile = tuple(state.play_pile)

        # 3. Public hand sizes (integers only)
        hand_sizes = {p: len(cards) for p, cards in state.hands.items()}

        # 4. Public declarations
        declarations = dict(state.last_card_declared)

        # 5. Public market count (integer only)
        market_size = len(state.market)

        # 6. Filtered event history
        if history is not None:
            public_events = tuple(e for e in history if e.is_public)
            private_events = tuple(
                e for e in history if not e.is_public and e.player == player_id
            )
        else:
            public_events = ()
            private_events = ()

        # 7. Action mask
        if player_id == state.current_player and not state.is_terminal:
            mask = tuple(RulesEngine.action_mask(state, player_id))
        else:
            # Not this player's turn: all actions masked out
            mask = tuple([0] * TOTAL_ACTIONS)

        return PlayerObservation(
            player_id=player_id,
            hand=own_hand,
            play_pile=public_play_pile,
            current_call=state.current_call,
            current_player=state.current_player,
            active_penalty_type=state.active_penalty_type,
            active_penalty_count=state.active_penalty_count,
            hand_sizes=hand_sizes,
            last_card_declared=declarations,
            market_size=market_size,
            public_history=public_events,
            private_events=private_events,
            action_mask=mask,
            ruleset=state.config,
            timestep=state.timestep,
            turn_count=state.turn_count,
            is_terminal=state.is_terminal,
            winner=state.winner,
        )
