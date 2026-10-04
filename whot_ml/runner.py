"""Headless game execution and batch tournament utilities for WHOT-ML (P0-D5)."""

from __future__ import annotations

from typing import Dict, List, Optional

from whot_ml.agents.base import Agent
from whot_ml.environment import GameEnvironment
from whot_ml.metrics import BatchMetrics, EpisodeMetrics, aggregate_metrics
from whot_ml.ruleset import WHOTConfig


def play_game(
    env: GameEnvironment,
    agents: Dict[int, Agent],
    seed: Optional[int] = None,
) -> EpisodeMetrics:
    """Execute a single complete game headlessly between the supplied agents.

    Each agent receives only its own PlayerObservation and selects an Action.
    Returns finalized EpisodeMetrics.
    """
    initial_obs = env.reset(seed=seed)

    for p, agent in agents.items():
        agent.reset(player_id=p, seed=seed)

    terminated = False
    truncated = False

    while not (terminated or truncated):
        curr_player = env.current_player
        obs = env.observe(curr_player)
        agent = agents[curr_player]

        action = agent.act(obs)
        step_result = env.step(action, acting_player=curr_player)

        terminated = step_result.terminated
        truncated = step_result.truncated

    return env.metrics_collector.metrics


def run_batch_evaluation(
    agents: Dict[int, Agent],
    num_games: int = 100,
    base_seed: int = 1000,
    config: Optional[WHOTConfig] = None,
) -> BatchMetrics:
    """Run a batch of independent seeded games and compute statistical summary."""
    env = GameEnvironment(config=config)
    episodes: List[EpisodeMetrics] = []

    for i in range(num_games):
        seed = base_seed + i
        ep_metrics = play_game(env, agents, seed=seed)
        episodes.append(ep_metrics)

    player_count = env.config.player_count
    return aggregate_metrics(episodes, player_count=player_count)
