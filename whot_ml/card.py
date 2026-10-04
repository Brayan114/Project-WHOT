"""Card, Shape, CardType, SpecialEffect, and Deck definitions for WHOT-ML."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class Shape(str, Enum):
    """The six shape identifiers defined in the WHOT ontology (P0-D3 Section 4)."""
    CIRCLE = "CIRCLE"
    TRIANGLE = "TRIANGLE"
    CROSS = "CROSS"
    SQUARE = "SQUARE"
    STAR = "STAR"
    WHOT = "WHOT"

    @property
    def is_ordinary(self) -> bool:
        """Return True if this is one of the five ordinary suits."""
        return self != Shape.WHOT

    @classmethod
    def ordinary_shapes(cls) -> Tuple[Shape, ...]:
        """Return the five ordinary suits available for matching and WHOT calls."""
        return (cls.CIRCLE, cls.TRIANGLE, cls.CROSS, cls.SQUARE, cls.STAR)


class CardType(str, Enum):
    """Card classification (P0-D3 Section 7)."""
    ORDINARY = "ORDINARY"
    WHOT = "WHOT"


class SpecialEffect(str, Enum):
    """Baseline card effects (P0-D1 Section 7, P0-D3 Section 8)."""
    HOLD_ON = "HOLD_ON"
    PICK_TWO = "PICK_TWO"
    PICK_THREE = "PICK_THREE"
    SUSPENSION = "SUSPENSION"
    GENERAL_MARKET = "GENERAL_MARKET"
    WILD_SHAPE = "WILD_SHAPE"


# Canonical value-to-effect mapping in baseline Nigerian WHOT
BASELINE_VALUE_EFFECTS: Dict[int, SpecialEffect] = {
    1: SpecialEffect.HOLD_ON,
    2: SpecialEffect.PICK_TWO,
    5: SpecialEffect.PICK_THREE,
    8: SpecialEffect.SUSPENSION,
    14: SpecialEffect.GENERAL_MARKET,
    20: SpecialEffect.WILD_SHAPE,
}

# 54-card deck distribution defined in P0-D1 Section 4 and P0-D3 Section 8
CANONICAL_DECK_SPEC: Dict[Shape, Tuple[int, ...]] = {
    Shape.CIRCLE: (1, 2, 3, 4, 5, 7, 8, 10, 11, 12, 13, 14),
    Shape.TRIANGLE: (1, 2, 3, 4, 5, 7, 8, 10, 11, 12, 13, 14),
    Shape.CROSS: (1, 2, 3, 5, 7, 10, 11, 13, 14),
    Shape.SQUARE: (1, 2, 3, 5, 7, 10, 11, 13, 14),
    Shape.STAR: (1, 2, 3, 4, 5, 7, 8),
}

NUM_WHOT_CARDS = 5
TOTAL_DECK_SIZE = 54
NUM_ORDINARY_CARDS = 49


@dataclass(frozen=True)
class Card:
    """Immutable representation of a physical card (P0-D3 Section 5).

    Every physical card in the deck possesses a unique immutable `id` and a
    canonical `card_index` in range [0, 53].
    """
    id: str
    card_index: int
    shape: Shape
    value: int
    card_type: CardType
    default_effect: Optional[SpecialEffect] = None

    def __post_init__(self) -> None:
        if not (0 <= self.card_index < TOTAL_DECK_SIZE):
            raise ValueError(f"card_index must be in [0, {TOTAL_DECK_SIZE - 1}], got {self.card_index}")
        if self.card_type == CardType.WHOT:
            if self.shape != Shape.WHOT or self.value != 20:
                raise ValueError("WHOT cards must have shape=WHOT and value=20")
        else:
            if not self.shape.is_ordinary:
                raise ValueError("Ordinary cards must possess an ordinary shape")

    @property
    def is_whot(self) -> bool:
        return self.card_type == CardType.WHOT

    def __str__(self) -> str:
        if self.is_whot:
            return f"[{self.id}: WHOT-20]"
        return f"[{self.id}: {self.shape.value} {self.value}]"

    def __repr__(self) -> str:
        return (
            f"Card(id={self.id!r}, index={self.card_index}, "
            f"shape={self.shape.value}, value={self.value})"
        )


def create_standard_deck() -> Tuple[Card, ...]:
    """Construct the canonical 54 physical cards of the Nigerian WHOT deck.

    Card index assignment:
      - 0 to 48: The 49 ordinary cards in deterministic order
                 (CIRCLE, TRIANGLE, CROSS, SQUARE, STAR by increasing value).
      - 49 to 53: The 5 WHOT cards (WHOT_1 to WHOT_5).
    """
    cards: List[Card] = []
    card_idx = 0

    # 1. Ordinary cards (49 total)
    for shape in Shape.ordinary_shapes():
        for val in CANONICAL_DECK_SPEC[shape]:
            card_id = f"{shape.value}_{val}"
            effect = BASELINE_VALUE_EFFECTS.get(val)
            cards.append(
                Card(
                    id=card_id,
                    card_index=card_idx,
                    shape=shape,
                    value=val,
                    card_type=CardType.ORDINARY,
                    default_effect=effect,
                )
            )
            card_idx += 1

    assert card_idx == NUM_ORDINARY_CARDS, f"Expected {NUM_ORDINARY_CARDS} ordinary cards, got {card_idx}"

    # 2. WHOT cards (5 total)
    for whot_num in range(1, NUM_WHOT_CARDS + 1):
        card_id = f"WHOT_{whot_num}"
        cards.append(
            Card(
                id=card_id,
                card_index=card_idx,
                shape=Shape.WHOT,
                value=20,
                card_type=CardType.WHOT,
                default_effect=SpecialEffect.WILD_SHAPE,
            )
        )
        card_idx += 1

    assert card_idx == TOTAL_DECK_SIZE, f"Expected {TOTAL_DECK_SIZE} total cards, got {card_idx}"
    return tuple(cards)


# Pre-instantiated immutable canonical deck and index lookups
CANONICAL_DECK: Tuple[Card, ...] = create_standard_deck()
CANONICAL_CARD_BY_ID: Dict[str, Card] = {c.id: c for c in CANONICAL_DECK}
CANONICAL_CARD_BY_INDEX: Dict[int, Card] = {c.card_index: c for c in CANONICAL_DECK}
