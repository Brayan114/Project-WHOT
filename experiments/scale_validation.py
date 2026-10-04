"""Scale validation and stress testing script for WHOT-NG-v1 (Phase 7).

Executes large batches of games (100 and 1,000 games) across multiple player counts
and baseline agent configurations, logging completion, legality, card conservation,
and special-card metrics.
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Any, Dict, List, Optional

from whot_ml.agents.base import Agent
from whot_ml.agents.random_agent import RandomLegalAgent
from whot_ml.agents.rule_based_agent import RuleBasedAgent
from whot_ml.environment import GameEnvironment
from whot_ml.metrics import EpisodeMetrics
from whot_ml.ruleset import WHOTConfig
from whot_ml.runner import play_game


def run_scale_experiment(
    agent_types: List[str],
    num_games: int,
    player_count: int = 4,
    base_seed: int = 10000,
    config: Optional[WHOTConfig] = None,
) -> Dict[str, Any]:
    """Execute a scale validation batch and print diagnostic progress."""
    cfg = (
        config
        if config is not None
        else WHOTConfig(player_count=player_count, debug_mode=True)
    )
    env = GameEnvironment(config=cfg)

    # Instantiate agents
    agents: Dict[int, Agent] = {}
    for p in range(player_count):
        atype = agent_types[p % len(agent_types)]
        if atype == "rule_based":
            agents[p] = RuleBasedAgent(name=f"RuleBased-{p}", seed=base_seed + p)
        else:
            agents[p] = RandomLegalAgent(name=f"Random-{p}", seed=base_seed + p)

    episodes: List[EpisodeMetrics] = []
    start_time = time.time()

    completed_victories = 0
    truncations = 0
    total_illegal = 0
    wins: Dict[int, int] = {p: 0 for p in range(player_count)}
    total_draws = 0
    total_whot = 0
    total_pick_two = 0
    total_pick_three = 0
    total_hold_on = 0
    total_suspensions = 0
    total_general_markets = 0
    total_declaration_violations = 0
    total_market_reshuffles = 0
    total_turns = 0

    print(
        f"\nStarting {num_games} games | {player_count} players | "
        f"Agents: {[a.name for a in agents.values()]} | Base Seed: {base_seed}"
    )

    for i in range(num_games):
        seed = base_seed + i
        ep = play_game(env, agents, seed=seed)
        episodes.append(ep)

        if ep.winner is not None:
            completed_victories += 1
            wins[ep.winner] += 1
        if ep.truncated:
            truncations += 1

        total_illegal += ep.illegal_action_count
        total_draws += ep.draw_count
        total_whot += ep.whot_plays
        total_pick_two += ep.pick_two_plays
        total_pick_three += ep.pick_three_plays
        total_hold_on += ep.hold_on_plays
        total_suspensions += ep.suspensions
        total_general_markets += ep.general_market_activations
        total_declaration_violations += ep.declaration_violations
        total_market_reshuffles += ep.market_reshuffles
        total_turns += ep.turn_count

        if (i + 1) % max(1, (num_games // 5)) == 0 or (i + 1) == num_games:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            print(f"  Processed {i + 1}/{num_games} games ({rate:.1f} games/sec)")

    elapsed = time.time() - start_time
    avg_turns = total_turns / num_games if num_games else 0.0

    results = {
        "num_games": num_games,
        "player_count": player_count,
        "agent_types": [a.name for a in agents.values()],
        "elapsed_seconds": elapsed,
        "games_per_second": num_games / elapsed if elapsed > 0 else 0,
        "completion_rate": completed_victories / num_games,
        "truncation_rate": truncations / num_games,
        "illegal_action_count": total_illegal,
        "average_game_length_turns": avg_turns,
        "wins_by_player": wins,
        "win_rates": {p: w / num_games for p, w in wins.items()},
        "total_draws": total_draws,
        "avg_draws_per_game": total_draws / num_games,
        "whot_plays": total_whot,
        "pick_two_plays": total_pick_two,
        "pick_three_plays": total_pick_three,
        "hold_on_plays": total_hold_on,
        "suspensions": total_suspensions,
        "general_market_activations": total_general_markets,
        "declaration_violations": total_declaration_violations,
        "market_reshuffles": total_market_reshuffles,
    }

    print("\n--- RESULTS ---")
    print(f"  Total Games: {num_games}")
    print(f"  Execution Time: {elapsed:.2f}s ({results['games_per_second']:.1f} games/sec)")
    print(f"  Completion Rate: {results['completion_rate']:.1%}")
    print(f"  Truncation Rate: {results['truncation_rate']:.1%}")
    print(f"  Illegal Actions: {results['illegal_action_count']}")
    print(f"  Average Game Length: {results['average_game_length_turns']:.2f} turns")
    print(f"  Wins by Player: {results['wins_by_player']}")
    print(f"  Win Rates: { {p: f'{r:.1%}' for p, r in results['win_rates'].items()} }")
    print(f"  Special Card Activations: WHOT={total_whot}, Pick2={total_pick_two}, Pick3={total_pick_three}, HoldOn={total_hold_on}, Susp={total_suspensions}, GeneralMarket={total_general_markets}")
    print(f"  Market Reshuffles: {total_market_reshuffles}")
    print(f"  Declaration Violations: {total_declaration_violations}")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="WHOT-ML Scale Validation Runner")
    parser.add_argument("--games", type=int, default=100, help="Number of games to simulate")
    parser.add_argument("--players", type=int, default=4, help="Number of players")
    parser.add_argument("--mode", choices=["random", "mixed", "rule_based"], default="mixed", help="Agent lineup")
    parser.add_argument("--seed", type=int, default=50000, help="Base seed")
    args = parser.parse_args()

    if args.mode == "random":
        agents = ["random"]
    elif args.mode == "rule_based":
        agents = ["rule_based"]
    else:
        # Mixed: 1 rule-based, remainder random
        agents = ["rule_based"] + ["random"] * (args.players - 1)

    run_scale_experiment(
        agent_types=agents,
        num_games=args.games,
        player_count=args.players,
        base_seed=args.seed,
    )


if __name__ == "__main__":
    main()
