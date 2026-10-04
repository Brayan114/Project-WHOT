"""Structured Event definitions for WHOT-ML (P0-D4 Section 35)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from whot_ml.card import Shape


class EventType(str, Enum):
    """Categorized event identifiers for public and private simulator event streams."""
    GAME_STARTED = "GAME_STARTED"
    CARD_PLAYED = "CARD_PLAYED"
    WHOT_SHAPE_SELECTED = "WHOT_SHAPE_SELECTED"
    CARD_DRAWN = "CARD_DRAWN"
    PENALTY_ACTIVATED = "PENALTY_ACTIVATED"
    PENALTY_STACKED = "PENALTY_STACKED"
    PENALTY_RESOLVED = "PENALTY_RESOLVED"
    GENERAL_MARKET_ACTIVATED = "GENERAL_MARKET_ACTIVATED"
    TURN_STARTED = "TURN_STARTED"
    TURN_SKIPPED = "TURN_SKIPPED"
    HOLD_ON_ACTIVATED = "HOLD_ON_ACTIVATED"
    LAST_CARD_DECLARED = "LAST_CARD_DECLARED"
    LAST_CARD_DECLARATION_VIOLATION = "LAST_CARD_DECLARATION_VIOLATION"
    MARKET_RESHUFFLED = "MARKET_RESHUFFLED"
    DRAW_UNAVAILABLE = "DRAW_UNAVAILABLE"
    ROUND_ENDED = "ROUND_ENDED"
    GAME_OVER = "GAME_OVER"
    ILLEGAL_ACTION = "ILLEGAL_ACTION"


@dataclass(frozen=True)
class Event:
    """An observable structured event emitted by the simulator."""
    event_type: EventType
    timestep: int
    player: Optional[int] = None
    card_id: Optional[str] = None
    shape: Optional[Shape] = None
    penalty_count: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        parts = [f"[{self.event_type.value} @ t={self.timestep}]"]
        if self.player is not None:
            parts.append(f"player={self.player}")
        if self.card_id is not None:
            parts.append(f"card={self.card_id}")
        if self.shape is not None:
            parts.append(f"shape={self.shape.value}")
        if self.penalty_count is not None:
            parts.append(f"penalty={self.penalty_count}")
        return " ".join(parts)
