"""Unit tests for Card and Deck foundations (P0-D1, P0-D3, P0-D4)."""

import pytest
from whot_ml.card import (
    CANONICAL_CARD_BY_ID,
    CANONICAL_CARD_BY_INDEX,
    CANONICAL_DECK,
    CANONICAL_DECK_SPEC,
    NUM_ORDINARY_CARDS,
    NUM_WHOT_CARDS,
    TOTAL_DECK_SIZE,
    Card,
    CardType,
    Shape,
    SpecialEffect,
    create_standard_deck,
)


def test_deck_total_count():
    """Verify that the standard Nigerian WHOT deck contains exactly 54 physical cards."""
    deck = create_standard_deck()
    assert len(deck) == TOTAL_DECK_SIZE
    assert len(CANONICAL_DECK) == 54


def test_card_ids_and_indices_are_unique():
    """Verify that all 54 physical cards have unique IDs and consecutive indices 0..53."""
    deck = CANONICAL_DECK
    ids = [c.id for c in deck]
    indices = [c.card_index for c in deck]

    assert len(set(ids)) == 54, "Card IDs must be strictly unique"
    assert indices == list(range(54)), "Card indices must be strictly 0 through 53"


def test_ordinary_and_whot_counts():
    """Verify 49 ordinary cards and 5 WHOT cards."""
    ordinary_cards = [c for c in CANONICAL_DECK if c.card_type == CardType.ORDINARY]
    whot_cards = [c for c in CANONICAL_DECK if c.card_type == CardType.WHOT]

    assert len(ordinary_cards) == NUM_ORDINARY_CARDS == 49
    assert len(whot_cards) == NUM_WHOT_CARDS == 5

    # Ordinary cards occupy indices 0..48
    for idx, c in enumerate(ordinary_cards):
        assert c.card_index == idx

    # WHOT cards occupy indices 49..53
    for offset, c in enumerate(whot_cards):
        assert c.card_index == 49 + offset


def test_distribution_per_shape():
    """Verify exact card distribution per shape matches specification:
    Circle: 12 cards (1,2,3,4,5,7,8,10,11,12,13,14)
    Triangle: 12 cards (1,2,3,4,5,7,8,10,11,12,13,14)
    Cross: 9 cards (1,2,3,5,7,10,11,13,14)
    Square: 9 cards (1,2,3,5,7,10,11,13,14)
    Star: 7 cards (1,2,3,4,5,7,8)
    WHOT: 5 cards (20 x 5)
    """
    for shape, expected_values in CANONICAL_DECK_SPEC.items():
        cards_of_shape = [c for c in CANONICAL_DECK if c.shape == shape]
        actual_values = tuple(c.value for c in cards_of_shape)
        assert actual_values == expected_values
        assert len(cards_of_shape) == len(expected_values)

    whot_cards = [c for c in CANONICAL_DECK if c.shape == Shape.WHOT]
    assert len(whot_cards) == 5
    assert all(c.value == 20 for c in whot_cards)
    assert all(c.is_whot for c in whot_cards)


def test_special_effect_assignments():
    """Verify baseline special effect mappings on physical cards."""
    # 1 -> HOLD_ON
    for c in CANONICAL_DECK:
        if c.value == 1:
            assert c.default_effect == SpecialEffect.HOLD_ON
        elif c.value == 2:
            assert c.default_effect == SpecialEffect.PICK_TWO
        elif c.value == 5:
            assert c.default_effect == SpecialEffect.PICK_THREE
        elif c.value == 8:
            assert c.default_effect == SpecialEffect.SUSPENSION
        elif c.value == 14:
            assert c.default_effect == SpecialEffect.GENERAL_MARKET
        elif c.value == 20:
            assert c.default_effect == SpecialEffect.WILD_SHAPE
        else:
            assert c.default_effect is None


def test_canonical_lookups():
    """Verify lookups by ID and index."""
    for c in CANONICAL_DECK:
        assert CANONICAL_CARD_BY_ID[c.id] == c
        assert CANONICAL_CARD_BY_INDEX[c.card_index] == c


def test_card_immutability():
    """Verify Card instances cannot be mutated."""
    c = CANONICAL_CARD_BY_INDEX[0]
    with pytest.raises(AttributeError):
        c.value = 99  # type: ignore
