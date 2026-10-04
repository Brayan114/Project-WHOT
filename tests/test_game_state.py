"""Unit tests for GameState creation, dealing, card conservation, and determinism."""

import pytest
from whot_ml.card import TOTAL_DECK_SIZE, Shape
from whot_ml.ruleset import InitialCardPolicy, StarterPolicy, WHOTConfig, get_baseline_config
from whot_ml.state import GameState


def test_initial_state_dealing_card_conservation():
    """Verify dealing distributes 24 cards across 4 players, 1 to play pile, 29 in market."""
    state = GameState.create_initial_state(seed=100)

    # Hand counts
    assert len(state.hands) == 4
    for p in range(4):
        assert len(state.hands[p]) == 6

    # Play pile & market
    assert len(state.play_pile) == 1
    assert len(state.market) == 54 - 24 - 1 == 29

    # Total cards conservation
    total = sum(len(h) for h in state.hands.values()) + len(state.play_pile) + len(state.market)
    assert total == TOTAL_DECK_SIZE == 54

    # Top card is ordinary or WHOT, current call is ordinary
    assert state.top_card == state.play_pile[0]
    assert state.current_call.is_ordinary


def test_starter_policy():
    """Verify fixed vs randomized starter policy."""
    cfg_fixed = WHOTConfig(starter_policy=StarterPolicy.FIXED_PLAYER_0)
    state_fixed = GameState.create_initial_state(config=cfg_fixed, seed=42)
    assert state_fixed.current_player == 0

    cfg_random = WHOTConfig(starter_policy=StarterPolicy.RANDOM)
    starters = {GameState.create_initial_state(config=cfg_random, seed=s).current_player for s in range(50)}
    assert len(starters) > 1, "Randomized starter policy should produce varied starters"


def test_initial_card_no_effect_baseline():
    """Verify that starting card's special effect does NOT activate during setup."""
    # Run multiple seeds to ensure starting cards with special values (1, 2, 5, 8, 14, 20) do not trigger
    for seed in range(20):
        state = GameState.create_initial_state(seed=seed)
        assert state.active_penalty_count == 0
        assert state.active_penalty_type is None
        assert state.current_call.is_ordinary
        # Hand counts remain exactly 6
        for p in range(4):
            assert len(state.hands[p]) == 6


def test_initial_state_deterministic_replay():
    """Verify that identical seeds produce bitwise identical initial states."""
    state_a = GameState.create_initial_state(seed=999)
    state_b = GameState.create_initial_state(seed=999)

    assert state_a.current_player == state_b.current_player
    assert state_a.current_call == state_b.current_call
    assert [c.id for c in state_a.play_pile] == [c.id for c in state_b.play_pile]
    assert [c.id for c in state_a.market] == [c.id for c in state_b.market]

    for p in range(4):
        assert [c.id for c in state_a.hands[p]] == [c.id for c in state_b.hands[p]]
