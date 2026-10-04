"""Multi-game batch evaluation tests across agents, seeds, and player counts (P0-D5)."""

import pytest
from whot_ml.agents.random_agent import RandomLegalAgent
from whot_ml.agents.rule_based_agent import RuleBasedAgent
from whot_ml.environment import GameEnvironment
from whot_ml.ruleset import WHOTConfig
from whot_ml.runner import play_game, run_batch_evaluation


def test_random_vs_random_batch_evaluation():
    """Verify 10 games between 4 RandomLegalAgents finish cleanly with zero illegal actions."""
    agents = {p: RandomLegalAgent(seed=100 + p) for p in range(4)}
    batch = run_batch_evaluation(agents, num_games=10, base_seed=5000)

    assert batch.games_played == 10
    assert sum(batch.wins_by_player.values()) + batch.truncations == 10
    assert batch.total_illegal_actions == 0
    assert batch.average_game_length > 0


def test_rule_based_vs_random_batch_evaluation():
    """Verify games between RuleBasedAgent and RandomLegalAgents complete cleanly."""
    agents = {
        0: RuleBasedAgent(name="RuleBased-0", seed=42),
        1: RandomLegalAgent(name="Random-1", seed=43),
        2: RandomLegalAgent(name="Random-2", seed=44),
        3: RandomLegalAgent(name="Random-3", seed=45),
    }
    batch = run_batch_evaluation(agents, num_games=10, base_seed=6000)

    assert batch.games_played == 10
    assert batch.total_illegal_actions == 0


def test_rule_based_vs_rule_based_batch_evaluation():
    """Verify 10 games between 4 RuleBasedAgents run cleanly."""
    agents = {p: RuleBasedAgent(name=f"RuleBased-{p}", seed=700 + p) for p in range(4)}
    batch = run_batch_evaluation(agents, num_games=10, base_seed=7000)

    assert batch.games_played == 10
    assert batch.total_illegal_actions == 0


def test_multiple_player_counts_support():
    """Verify that 2, 3, 4, and 6 player games run without error."""
    for n_players in (2, 3, 4, 6):
        cfg = WHOTConfig(player_count=n_players, starting_hand_size=5)
        env = GameEnvironment(config=cfg)
        agents = {p: RandomLegalAgent(seed=p) for p in range(n_players)}

        metrics = play_game(env, agents, seed=8888 + n_players)
        assert metrics.turn_count > 0
        assert metrics.illegal_action_count == 0
        assert metrics.winner is not None or metrics.truncated


def test_full_game_deterministic_replay():
    """Verify that running a complete game twice with identical seed produces identical results."""
    cfg = WHOTConfig()
    env1 = GameEnvironment(config=cfg)
    agents1 = {p: RandomLegalAgent(seed=p) for p in range(4)}
    m1 = play_game(env1, agents1, seed=4242)

    env2 = GameEnvironment(config=cfg)
    agents2 = {p: RandomLegalAgent(seed=p) for p in range(4)}
    m2 = play_game(env2, agents2, seed=4242)

    assert m1.winner == m2.winner
    assert m1.turn_count == m2.turn_count
    assert m1.final_hand_sizes == m2.final_hand_sizes
    assert [e.event_type for e in env1.history] == [e.event_type for e in env2.history]
