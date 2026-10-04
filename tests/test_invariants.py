"""Unit tests for InvariantValidator and diagnostic failure reporting."""

import pytest
from whot_ml.card import CANONICAL_CARD_BY_INDEX, Shape
from whot_ml.invariants import InvariantValidator, InvariantViolationError
from whot_ml.state import GameState


def test_valid_state_passes_invariants():
    """Verify that a freshly initialized state passes all invariant checks."""
    state = GameState.create_initial_state(seed=42)
    # Should not raise
    InvariantValidator.validate(state)


def test_card_conservation_failure():
    """Verify error raised when card count does not equal 54."""
    state = GameState.create_initial_state(seed=42)
    # Artificially delete a card
    state.market.pop()
    with pytest.raises(InvariantViolationError) as exc_info:
        InvariantValidator.validate(state)
    assert "Card conservation failed" in str(exc_info.value)


def test_duplicate_card_failure():
    """Verify error raised when a card appears in two places."""
    state = GameState.create_initial_state(seed=42)
    # Duplicate player 0's first card into player 1's hand
    duplicate_card = state.hands[0][0]
    state.hands[1].append(duplicate_card)
    state.market.pop()  # Keep total count 54, but with a duplicate
    with pytest.raises(InvariantViolationError) as exc_info:
        InvariantValidator.validate(state)
    assert "Duplicate card" in str(exc_info.value)


def test_invalid_current_player_failure():
    """Verify error raised when current player is out of range."""
    state = GameState.create_initial_state(seed=42)
    state.current_player = 99
    with pytest.raises(InvariantViolationError) as exc_info:
        InvariantValidator.validate(state)
    assert "Current player" in str(exc_info.value)


def test_invalid_current_call_failure():
    """Verify error raised when current call is not ordinary."""
    state = GameState.create_initial_state(seed=42)
    state.current_call = Shape.WHOT  # Invalid call
    with pytest.raises(InvariantViolationError) as exc_info:
        InvariantValidator.validate(state)
    assert "Current call must be an ordinary shape" in str(exc_info.value)
