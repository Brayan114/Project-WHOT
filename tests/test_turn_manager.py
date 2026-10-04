"""Unit tests for TurnManager progression, modifiers, and direction (P0-D1, P0-D4)."""

import pytest
from whot_ml.ruleset import TurnDirection
from whot_ml.turn_manager import TurnManager, TurnModifier


def test_clockwise_normal_progression():
    """Verify clockwise progression advances to next sequential player."""
    # 4 players: 0 -> 1 -> 2 -> 3 -> 0
    next_p, skipped = TurnManager.advance_player(
        current_player=0, num_players=4, direction=TurnDirection.CLOCKWISE, modifier=TurnModifier.NORMAL
    )
    assert next_p == 1
    assert skipped is None

    next_p, skipped = TurnManager.advance_player(
        current_player=3, num_players=4, direction=TurnDirection.CLOCKWISE, modifier=TurnModifier.NORMAL
    )
    assert next_p == 0
    assert skipped is None


def test_counter_clockwise_normal_progression():
    """Verify counter-clockwise progression advances in reverse."""
    next_p, skipped = TurnManager.advance_player(
        current_player=0, num_players=4, direction=TurnDirection.COUNTER_CLOCKWISE, modifier=TurnModifier.NORMAL
    )
    assert next_p == 3
    assert skipped is None


def test_extra_turn_hold_on():
    """Verify Hold On (Card 1) keeps current player active."""
    for p in range(4):
        next_p, skipped = TurnManager.advance_player(
            current_player=p, num_players=4, direction=TurnDirection.CLOCKWISE, modifier=TurnModifier.EXTRA_TURN
        )
        assert next_p == p
        assert skipped is None


def test_suspension_skip_next():
    """Verify Suspension (Card 8) skips the next player in order."""
    # In 4-player clockwise: player 0 plays 8 -> player 1 skipped -> player 2 acts
    next_p, skipped = TurnManager.advance_player(
        current_player=0, num_players=4, direction=TurnDirection.CLOCKWISE, modifier=TurnModifier.SKIP_NEXT
    )
    assert next_p == 2
    assert skipped == 1

    # Wrapping around: player 3 plays 8 -> player 0 skipped -> player 1 acts
    next_p, skipped = TurnManager.advance_player(
        current_player=3, num_players=4, direction=TurnDirection.CLOCKWISE, modifier=TurnModifier.SKIP_NEXT
    )
    assert next_p == 1
    assert skipped == 0

    # 2-player game: player 0 plays 8 -> player 1 skipped -> player 0 acts again
    next_p, skipped = TurnManager.advance_player(
        current_player=0, num_players=2, direction=TurnDirection.CLOCKWISE, modifier=TurnModifier.SKIP_NEXT
    )
    assert next_p == 0
    assert skipped == 1


def test_general_market_recipients_order():
    """Verify General Market produces deterministic clockwise recipient sequence."""
    recipients = TurnManager.get_recipients_in_order(
        current_player=0, num_players=4, direction=TurnDirection.CLOCKWISE
    )
    assert recipients == [1, 2, 3]

    recipients_from_2 = TurnManager.get_recipients_in_order(
        current_player=2, num_players=4, direction=TurnDirection.CLOCKWISE
    )
    assert recipients_from_2 == [3, 0, 1]
