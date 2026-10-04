"""Structured Event definitions and public/private visibility for WHOT-ML (P0-D4 Section 35)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from whot_ml.card import Shape


class EventType(str, Enum):
    """Categorized event identifiers for public and private simulator event streams."""
    # Public events
    GAME_STARTED = "GAME_STARTED"
    CARD_PLAYED = "CARD_PLAYED"
    WHOT_SHAPE_SELECTED = "WHOT_SHAPE_SELECTED"
    CARD_DRAWN = "CARD_DRAWN"  # Public count/event; card_id must be None
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

    # Private events (only visible to the specific recipient)
    PRIVATE_CARD_RECEIVED = "PRIVATE_CARD_RECEIVED"


@dataclass(frozen=True)
class Event:
    """An observable structured event emitted by the simulator."""
    event_type: EventType
    timestep: int
    player: Optional[int] = None
    card_id: Optional[str] = None
    shape: Optional[Shape] = None
    penalty_count: Optional[int] = None
    is_public: bool = True
    details: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.is_public and self.event_type == EventType.CARD_DRAWN and self.card_id is not None:
            raise ValueError(
                "Public CARD_DRAWN event must NOT leak card_id. Use PRIVATE_CARD_RECEIVED for card identity."
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to serializable dictionary."""
        return {
            "event_type": self.event_type.value,
            "timestep": self.timestep,
            "player": self.player,
            "card_id": self.card_id,
            "shape": self.shape.value if self.shape else None,
            "penalty_count": self.penalty_count,
            "is_public": self.is_public,
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Event:
        """Reconstruct event from dictionary."""
        d = dict(data)
        d["event_type"] = EventType(d["event_type"])
        if d.get("shape"):
            d["shape"] = Shape(d["shape"])
        return cls(**d)

    def __str__(self) -> str:
        vis = "PUBLIC" if self.is_public else "PRIVATE"
        parts = [f"[{self.event_type.value} ({vis}) @ t={self.timestep}]"]
        if self.player is not None:
            parts.append(f"player={self.player}")
        if self.card_id is not None:
            parts.append(f"card={self.card_id}")
        if self.shape is not None:
            parts.append(f"shape={self.shape.value}")
        if self.penalty_count is not None:
            parts.append(f"penalty={self.penalty_count}")
        return " ".join(parts)
