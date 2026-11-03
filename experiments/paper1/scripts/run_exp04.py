"""EXP-04: Player Count Scaling (Stage 3B).

Evaluates how game length, draw rate, and hidden-to-visible card metrics scale
as player count varies across N in {2, 3, 4, 5, 6}.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.paper1.scripts.common import (
    BalancedSeatAssigner,
    GameTrajectoryRecord,
    RunManifest,
    StatisticalUtilities,
    TrajectoryCollector,
    compute_config_hash,
    load_experiment_config,
    save_processed_metrics,
    save_raw_telemetry,
)
from whot_ml.environment import GameEnvironment
from whot_ml.ruleset import WHOTConfig, get_baseline_config


def _run_exp04_game(args: Tuple[str, bool, bool, int, int, str, str, int]) -> GameTrajectoryRecord:
    """Worker task executing a single game in EXP-04."""
    exp_id, pilot, dry_run, seed, n, cfg_hash, agent_type, g = args
    whot_config = WHOTConfig(player_count=n)
    manifest = RunManifest(
        experiment_id=f"{exp_id}-N{n}",
        is_pilot=pilot if not dry_run else False,
        is_dry_run=dry_run,
        seed=seed,
        player_count=n,
        ruleset_hash=cfg_hash,
        config_hash=cfg_hash,
        agent_population=[agent_type] * n,
    )

    env = GameEnvironment(config=whot_config)
    agents = BalancedSeatAssigner.assign_seats(
        agent_types=[agent_type] * n,
        game_index=g,
        base_seed=seed,
        rotate=True,
    )

    return TrajectoryCollector.play_instrumented_game(
        env=env,
        agents=agents,
        manifest=manifest,
        record_steps=False,
    )


def run_exp04(
    pilot: bool = True,
    dry_run: bool = False,
    config_filename: str = "exp04_player_scaling.json",
    output_tag: Optional[str] = None,
    workers: int = 1,
) -> Dict[str, Any]:
    """Execute EXP-04 Player Count Scaling."""
    config_data = load_experiment_config(config_filename)
    exp_id = config_data["experiment_id"]
    player_counts = config_data["player_counts"]
    agent_type = config_data.get("agent_type", "rule_based")
    if dry_run:
        games_per_n = 2
        suffix = "dry_run"
    else:
        games_per_n = (
            config_data["pilot_games_per_n"] if pilot else config_data["full_games_per_n"]
        )
        suffix = "pilot" if pilot else "full"
    seed_base = config_data["pilot_seed_base"] if (pilot or dry_run) else config_data["full_seed_base"]

    mode_label = "DRY-RUN" if dry_run else ("PILOT" if pilot else "FULL")
    print(f"\n[{exp_id}] Starting Player Count Scaling ({mode_label})")
    print(f"  Player counts: {player_counts} | Games per N: {games_per_n} | Agent: {agent_type} | Workers: {workers}")

    all_records: List[GameTrajectoryRecord] = []
    scaling_results: Dict[str, Any] = {}

    for n in player_counts:
        print(f"\n  Evaluating N = {n} players...")
        whot_config = WHOTConfig(player_count=n)
        cfg_hash = compute_config_hash(whot_config)

        # Theoretical information metrics at deal
        init_mkt = 54 - 6 * n - 1
        init_opp = 6 * (n - 1)
        init_ratio = round(init_opp / init_mkt, 4) if init_mkt > 0 else float("inf")

        turn_counts: List[int] = []
        turns_per_player: List[float] = []
        draw_counts: List[int] = []
        draws_per_player: List[float] = []
        reshuffle_counts: List[int] = []
        truncations = 0

        task_args = [
            (exp_id, pilot, dry_run, seed_base + g, n, cfg_hash, agent_type, g)
            for g in range(games_per_n)
        ]

        if workers > 1:
            with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
                recs = list(executor.map(_run_exp04_game, task_args))
        else:
            recs = [_run_exp04_game(a) for a in task_args]

        for rec in recs:
            all_records.append(rec)
            turn_counts.append(rec.turn_count)
            turns_per_player.append(rec.turn_count / n)
            draw_counts.append(rec.draw_count)
            draws_per_player.append(rec.draw_count / n)
            reshuffle_counts.append(rec.market_reshuffles)
            if rec.truncated:
                truncations += 1

        scaling_results[str(n)] = {
            "player_count": n,
            "initial_market_size": init_mkt,
            "initial_opponent_cards": init_opp,
            "initial_opp_to_market_ratio": init_ratio,
            "games_played": games_per_n,
            "turn_count": StatisticalUtilities.calculate_scalar_stats(turn_counts),
            "turns_per_player": StatisticalUtilities.calculate_scalar_stats(turns_per_player),
            "draw_count": StatisticalUtilities.calculate_scalar_stats(draw_counts),
            "draws_per_player": StatisticalUtilities.calculate_scalar_stats(draws_per_player),
            "market_reshuffles": StatisticalUtilities.calculate_scalar_stats(reshuffle_counts),
            "truncation": StatisticalUtilities.wilson_score_interval(truncations, games_per_n),
        }

    tag = output_tag
    if not tag:
        if "04a" in config_filename:
            tag = "exp04a"
        elif "04b" in config_filename:
            tag = "exp04b"
        else:
            tag = "exp04"

    raw_path = save_raw_telemetry(f"{tag}_{suffix}_raw.jsonl", all_records)

    processed_data = {
        "experiment_id": exp_id,
        "is_pilot": pilot if not dry_run else False,
        "is_dry_run": dry_run,
        "agent_type": agent_type,
        "scaling_results": scaling_results,
    }
    processed_path = save_processed_metrics(f"{tag}_{suffix}_summary.json", processed_data)

    print(f"\n[{exp_id}] Finished successfully.")
    print(f"  Raw data: {raw_path}")
    print(f"  Processed metrics: {processed_path}")

    return processed_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run EXP-04")
    parser.add_argument(
        "--full", action="store_true", help="Run full experiment instead of pilot"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run small dry-run test"
    )
    parser.add_argument(
        "--config", default="exp04_player_scaling.json", help="Configuration file"
    )
    parser.add_argument(
        "--tag", default=None, help="Output file prefix tag (e.g. exp04a, exp04b)"
    )
    parser.add_argument(
        "--workers", type=int, default=1, help="Number of parallel worker processes"
    )
    args = parser.parse_args()
    run_exp04(
        pilot=not args.full,
        dry_run=args.dry_run,
        config_filename=args.config,
        output_tag=args.tag,
        workers=args.workers,
    )
