"""Reproducibility protocol and determinism audit tests (P0-D5 Section 2, 7, 8)."""

import pytest
from whot_ml.agents.random_agent import RandomLegalAgent
from whot_ml.agents.rule_based_agent import RuleBasedAgent
from whot_ml.environment import GameEnvironment
from whot_ml.ruleset import WHOTConfig
from whot_ml.runner import play_game, run_batch_evaluation
from whot_ml.serializer import restore_state, serialize_state


def test_seed_determinism_full_game_trajectory():
    """Verify that same seed + same ruleset + same agents yields identical action and event sequence."""
    cfg = WHOTConfig()

    env1 = GameEnvironment(config=cfg)
    agents1 = {p: RandomLegalAgent(seed=10 + p) for p in range(4)}
    m1 = play_game(env1, agents1, seed=99999)

    env2 = GameEnvironment(config=cfg)
    agents2 = {p: RandomLegalAgent(seed=10 + p) for p in range(4)}
    m2 = play_game(env2, agents2, seed=99999)

    assert m1.winner == m2.winner
    assert m1.turn_count == m2.turn_count
    assert m1.timestep == m2.timestep
    assert m1.final_hand_sizes == m2.final_hand_sizes
    assert [e.to_dict() for e in env1.history] == [e.to_dict() for e in env2.history]


def test_different_seeds_produce_different_trajectories():
    """Verify that different seeds produce genuinely distinct initial cards and outcomes."""
    cfg = WHOTConfig()

    env1 = GameEnvironment(config=cfg)
    agents1 = {p: RandomLegalAgent(seed=p) for p in range(4)}
    m1 = play_game(env1, agents1, seed=1111)

    env2 = GameEnvironment(config=cfg)
    agents2 = {p: RandomLegalAgent(seed=p) for p in range(4)}
    m2 = play_game(env2, agents2, seed=2222)

    # Hand setups and trajectories must differ
    h1 = [e.to_dict() for e in env1.history]
    h2 = [e.to_dict() for e in env2.history]
    assert h1 != h2


def test_state_serialization_and_resumed_continuation():
    """Verify that pausing a game mid-way, serializing, restoring, and continuing produces
    the exact same future game as continuing without serialization.
    """
    cfg = WHOTConfig()
    env_continue = GameEnvironment(config=cfg)
    env_continue.reset(seed=7777)
    agents = {p: RandomLegalAgent(seed=100 + p) for p in range(4)}

    # Play 10 steps in env_continue
    for _ in range(10):
        if env_continue.is_terminal:
            break
        curr = env_continue.current_player
        action = agents[curr].act(env_continue.observe(curr))
        env_continue.step(action, acting_player=curr)

    # Checkpoint state
    checkpoint = env_continue.serialize_state()

    # Create resumed environment
    env_resumed = GameEnvironment(config=cfg)
    env_resumed.restore_state(checkpoint)

    # Reset agent copies with identical seeds from checkpoint
    agents_cont = {p: RandomLegalAgent(seed=200 + p) for p in range(4)}
    agents_resumed = {p: RandomLegalAgent(seed=200 + p) for p in range(4)}

    # Play 15 more steps on both
    for _ in range(15):
        if env_continue.is_terminal:
            break
        c_cont = env_continue.current_player
        c_res = env_resumed.current_player
        assert c_cont == c_res

        a_cont = agents_cont[c_cont].act(env_continue.observe(c_cont))
        a_res = agents_resumed[c_res].act(env_resumed.observe(c_res))
        assert a_cont == a_res

        env_continue.step(a_cont, acting_player=c_cont)
        env_resumed.step(a_res, acting_player=c_res)

        # Both states must remain bitwise identical
        assert env_continue.state.current_player == env_resumed.state.current_player
        assert env_continue.state.current_call == env_resumed.state.current_call
        assert [c.id for c in env_continue.state.play_pile] == [c.id for c in env_resumed.state.play_pile]
        assert [c.id for c in env_continue.state.market] == [c.id for c in env_resumed.state.market]


def test_batch_schedule_reproducibility():
    """Verify that a batch evaluation reproduces the exact same summary across runs."""
    agents1 = {p: RuleBasedAgent(name=f"R-{p}", seed=p) for p in range(4)}
    b1 = run_batch_evaluation(agents1, num_games=10, base_seed=8000)

    agents2 = {p: RuleBasedAgent(name=f"R-{p}", seed=p) for p in range(4)}
    b2 = run_batch_evaluation(agents2, num_games=10, base_seed=8000)

    assert b1.wins_by_player == b2.wins_by_player
    assert b1.average_game_length == b2.average_game_length
    assert b1.truncations == b2.truncations
