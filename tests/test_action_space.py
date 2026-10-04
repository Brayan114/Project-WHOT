"""Unit tests for the Frozen 76-Action Space (P0-D2, P0-D4)."""

import pytest
from whot_ml.action import (
    ACTION_INDEX_DECLARE_LAST,
    ACTION_INDEX_DRAW,
    INDEX_TO_ACTION,
    ORDINARY_SHAPES,
    TOTAL_ACTIONS,
    Action,
    ActionType,
    action_to_index,
    index_to_action,
    make_declare_last_action,
    make_draw_action,
    make_play_card_action,
    make_play_whot_action,
)
from whot_ml.card import (
    CANONICAL_CARD_BY_INDEX,
    CANONICAL_DECK,
    NUM_ORDINARY_CARDS,
    NUM_WHOT_CARDS,
    CardType,
    Shape,
)


def test_action_space_size():
    """Verify the action space has exactly 76 discrete actions."""
    assert TOTAL_ACTIONS == 76
    assert len(INDEX_TO_ACTION) == 76


def test_actions_0_to_48_play_ordinary():
    """Verify actions 0..48 are PLAY actions for the 49 ordinary cards."""
    for action_id in range(49):
        action = index_to_action(action_id)
        card = CANONICAL_CARD_BY_INDEX[action_id]

        assert action.action_type == ActionType.PLAY
        assert action.action_id == action_id
        assert action.card_id == card.id
        assert action.card_index == card.card_index
        assert action.selected_shape is None
        assert card.card_type == CardType.ORDINARY


def test_actions_49_to_73_play_whot():
    """Verify actions 49..73 are PLAY_WHOT actions:
    5 WHOT cards x 5 shapes = 25 actions.
    """
    assert NUM_WHOT_CARDS * len(ORDINARY_SHAPES) == 25

    expected_action_id = 49
    for whot_idx in range(NUM_ORDINARY_CARDS, NUM_ORDINARY_CARDS + NUM_WHOT_CARDS):
        whot_card = CANONICAL_CARD_BY_INDEX[whot_idx]
        assert whot_card.card_type == CardType.WHOT

        for shape in ORDINARY_SHAPES:
            action = index_to_action(expected_action_id)
            assert action.action_type == ActionType.PLAY_WHOT
            assert action.action_id == expected_action_id
            assert action.card_id == whot_card.id
            assert action.card_index == whot_idx
            assert action.selected_shape == shape
            expected_action_id += 1

    assert expected_action_id == 74


def test_action_74_draw():
    """Verify action 74 is DRAW."""
    action = index_to_action(74)
    assert action.action_type == ActionType.DRAW
    assert action.action_id == ACTION_INDEX_DRAW
    assert action.card_id is None
    assert action.selected_shape is None


def test_action_75_declare_last():
    """Verify action 75 is DECLARE_LAST."""
    action = index_to_action(75)
    assert action.action_type == ActionType.DECLARE_LAST
    assert action.action_id == ACTION_INDEX_DECLARE_LAST
    assert action.card_id is None
    assert action.selected_shape is None


def test_bidirectional_mapping():
    """Verify that every action index round-trips perfectly."""
    for action_id in range(TOTAL_ACTIONS):
        action = index_to_action(action_id)
        assert action_to_index(action) == action_id


def test_action_helpers():
    """Verify helper constructors for creating actions."""
    # Ordinary play helper
    card_0 = CANONICAL_CARD_BY_INDEX[0]
    act_0 = make_play_card_action(card_0)
    assert act_0.action_id == 0
    assert act_0.action_type == ActionType.PLAY

    # WHOT play helper
    whot_card = CANONICAL_CARD_BY_INDEX[49]
    act_whot_star = make_play_whot_action(whot_card, Shape.STAR)
    expected_id = 49 + 0 * 5 + ORDINARY_SHAPES.index(Shape.STAR)
    assert act_whot_star.action_id == expected_id
    assert act_whot_star.selected_shape == Shape.STAR

    # Draw helper
    act_draw = make_draw_action()
    assert act_draw.action_id == 74
    assert act_draw.action_type == ActionType.DRAW

    # Declare helper
    act_declare = make_declare_last_action()
    assert act_declare.action_id == 75
    assert act_declare.action_type == ActionType.DECLARE_LAST


def test_invalid_actions_raise_errors():
    """Verify out-of-range action indices and invalid configurations raise errors."""
    with pytest.raises(IndexError):
        index_to_action(-1)

    with pytest.raises(IndexError):
        index_to_action(76)

    # Cannot create WHOT action on ordinary card
    card_0 = CANONICAL_CARD_BY_INDEX[0]
    with pytest.raises(ValueError):
        make_play_whot_action(card_0, Shape.STAR)

    # Cannot create ordinary action on WHOT card
    whot_card = CANONICAL_CARD_BY_INDEX[49]
    with pytest.raises(ValueError):
        make_play_card_action(whot_card)

    # Cannot select WHOT as shape for WHOT play
    with pytest.raises(ValueError):
        make_play_whot_action(whot_card, Shape.WHOT)
