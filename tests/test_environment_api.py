"""Unit tests for high-level GameEnvironment API (P0-D4 Section 33)."""

import pytest
from whot_ml.action import ActionType, make_draw_action
from whot_ml.environment import GameEnvironment
from whot_ml.rules_engine import IllegalActionError
from whot_ml.ruleset import WHOTConfig


def test_environment_reset_and_observe():
    """Verify reset() initializes all players and observe() returns valid observations."""
    env = GameEnvironment()
    obs_dict = env.reset(seed=42)

    assert len(obs_dict) == 4
    for p in range(4):
        obs = env.observe(p)
        assert obs.player_id == p
        assert len(obs.hand) == 6
        assert obs.market_size == 29
        assert obs.current_player == env.current_player
        assert obs.top_card == env.state.top_card


def test_environment_step_advances_turn():
    """Verify step() executes action and returns EnvStepResult."""
    env = GameEnvironment()
    env.reset(seed=42)

    curr_p = env.current_player
    actions = env.legal_actions(curr_p)
    assert len(actions) > 0

    first_action = actions[0]
    result = env.step(first_action, acting_player=curr_p)

    assert result.acting_player == curr_p
    assert isinstance(result.rewards, dict)
    assert not result.terminated or env.is_terminal
    assert result.next_player == env.current_player


def test_out_of_turn_action_rejected():
    """Verify that a player acting out of turn is rejected without mutating state."""
    env = GameEnvironment()
    env.reset(seed=42)

    curr = env.current_player
    non_curr = (curr + 1) % 4

    actions = env.legal_actions(curr)
    action = actions[0]

    with pytest.raises(IllegalActionError):
        env.step(action, acting_player=non_curr)

    # State must be unchanged
    assert env.current_player == curr
    assert env.state.timestep == 0


def test_truncation_enforcement():
    """Verify that reaching maximum_turns sets truncated=True."""
    short_config = WHOTConfig(maximum_turns=12)
    env = GameEnvironment(config=short_config)
    env.reset(seed=42)

    # Fast-forward turn count to 12
    env.state.turn_count = 11
    curr = env.current_player
    actions = env.legal_actions(curr)

    result = env.step(actions[0], acting_player=curr)
    assert result.truncated is True
    assert env.is_terminal is True


def test_environment_serialization_round_trip():
    """Verify serialize_state() and restore_state() on environment."""
    env = GameEnvironment()
    env.reset(seed=42)

    # Step once
    curr = env.current_player
    env.step(env.legal_actions(curr)[0], acting_player=curr)

    checkpoint = env.serialize_state()

    env2 = GameEnvironment()
    env2.restore_state(checkpoint)

    assert env2.current_player == env.current_player
    assert env2.state.current_call == env.state.current_call
    assert len(env2.state.market) == len(env.state.market)
    assert [c.id for c in env2.state.play_pile] == [c.id for c in env.state.play_pile]
