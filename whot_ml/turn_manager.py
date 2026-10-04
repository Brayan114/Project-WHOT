"""Turn management, sequencing, and modifiers for WHOT-ML (P0-D1, P0-D4)."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Tuple

from whot_ml.ruleset import TurnDirection


class TurnModifier(str, Enum):
    """Temporary turn modifications produced by action cards (P0-D4 Section 11)."""
    NORMAL = "NORMAL"
    EXTRA_TURN = "EXTRA_TURN"  # Produced by Hold On (Card 1)
    SKIP_NEXT = "SKIP_NEXT"    # Produced by Suspension (Card 8)


class TurnManager:
    """Manages player progression, directional turns, suspensions, and extra turns."""

    @staticmethod
    def step_delta(direction: TurnDirection) -> int:
        """Return index delta based on current turn direction."""
        return 1 if direction == TurnDirection.CLOCKWISE else -1

    @classmethod
    def advance_player(
        cls,
        current_player: int,
        num_players: int,
        direction: TurnDirection = TurnDirection.CLOCKWISE,
        modifier: TurnModifier = TurnModifier.NORMAL,
    ) -> Tuple[int, Optional[int]]:
        """Compute next acting player and any skipped player.

        Returns:
            Tuple of (next_player_id, skipped_player_id_or_None)
        """
        if num_players < 2:
            raise ValueError(f"num_players must be >= 2, got {num_players}")
        if not (0 <= current_player < num_players):
            raise ValueError(f"current_player {current_player} out of range for {num_players} players")

        if modifier == TurnModifier.EXTRA_TURN:
            # Hold On: same player receives another turn (P0-D1 Section 8, P0-D4 Section 11.2)
            return current_player, None

        step = cls.step_delta(direction)

        if modifier == TurnModifier.SKIP_NEXT:
            # Suspension: next player loses turn, play moves to following player (P0-D4 Section 11.3)
            skipped = (current_player + step) % num_players
            next_player = (current_player + 2 * step) % num_players
            return next_player, skipped

        # Normal progression
        next_player = (current_player + step) % num_players
        return next_player, None

    @classmethod
    def get_recipients_in_order(
        cls,
        current_player: int,
        num_players: int,
        direction: TurnDirection = TurnDirection.CLOCKWISE,
    ) -> List[int]:
        """Return all other players in turn order starting from next player.

        Used for General Market (14) resolution (P0-D4 Section 23).
        """
        step = cls.step_delta(direction)
        recipients: List[int] = []
        curr = (current_player + step) % num_players
        while curr != current_player:
            recipients.append(curr)
            curr = (curr + step) % num_players
        return recipients
