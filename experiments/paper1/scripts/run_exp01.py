"""EXP-01: Environment Characterization (Stage 3B).

Quantifies structural and behavioral distributions of WHOT-NG-v1 across decision states,
turn durations, card draws, and special-card activations under baseline play.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.paper1.scripts.common import (
    BalancedSeatAssigner,
    GameTrajectoryRecord,
    RunManifest,
    StatisticalUtilities,
    StreamTelemetryWriter,
    TrajectoryCollector,
    compute_config_hash,
    load_experiment_config,
    save_processed_metrics,
    save_raw_telemetry,
)
from whot_ml.environment import GameEnvironment
from whot_ml.ruleset import WHOTConfig, get_baseline_config


def run_exp01(pilot: bool = True, dry_run: bool = False) -> Dict[str, Any]:
    """Execute EXP-01 Environment Characterization."""
    config_data = load_experiment_config("exp01_characterization.json")
    exp_id = config_data["experiment_id"]
    if dry_run:
        games_per_cohort = 5
        suffix = "dry_run"
    else:
        games_per_cohort = (
            config_data["pilot_games_per_cohort"] if pilot else config_data["full_games_per_cohort"]
        )
        suffix = "pilot" if pilot else "full"

    seed_base = config_data["pilot_seed_base"] if (pilot or dry_run) else config_data["full_seed_base"]
    player_count = config_data["player_count"]

    whot_config = WHOTConfig(player_count=player_count)
    config_hash = compute_config_hash(whot_config)

    mode_label = "DRY-RUN" if dry_run else ("PILOT" if pilot else "FULL")
    print(
        f"\n[EXP-01] Starting Environment Characterization ({mode_label})"
    )
    print(f"  Games per cohort: {games_per_cohort} | Player count: {player_count}")

    cohort_results: Dict[str, Any] = {}
    raw_filename = f"exp01_{suffix}_raw.jsonl"

    with StreamTelemetryWriter(raw_filename) as writer:
        for cohort in config_data["cohorts"]:
            cohort_name = cohort["name"]
            agent_type = cohort["agent_type"]
            seed_offset = cohort["seed_offset"]
            print(f"\n  Running cohort: {cohort_name} ({agent_type})")

            cohort_records: List[GameTrajectoryRecord] = []
            turn_counts: List[int] = []
            draw_counts: List[int] = []
            all_legal_counts: List[int] = []
            hand_sizes_across_steps: List[int] = []
            whot_plays_list: List[int] = []
            pick_two_list: List[int] = []
            pick_three_list: List[int] = []
            hold_on_list: List[int] = []
            suspension_list: List[int] = []
            gen_market_list: List[int] = []
            declaration_violations_list: List[int] = []
            market_reshuffles_list: List[int] = []
            truncation_count = 0

            for g in range(games_per_cohort):
                seed = seed_base + seed_offset + g
                manifest = RunManifest(
                    experiment_id=exp_id,
                    is_pilot=pilot if not dry_run else False,
                    is_dry_run=dry_run,
                    seed=seed,
                    player_count=player_count,
                    variant_id="VAR-BASE",
                    ruleset_hash=config_hash,
                    config_hash=config_hash,
                    agent_population=[agent_type] * player_count,
                )

                env = GameEnvironment(config=whot_config)
                agents = BalancedSeatAssigner.assign_seats(
                    agent_types=[agent_type] * player_count,
                    game_index=g,
                    base_seed=seed,
                    rotate=False,
                )

                rec = TrajectoryCollector.play_instrumented_game(
                    env=env,
                    agents=agents,
                    manifest=manifest,
                    record_steps=True,
                )

                writer.write_record(rec)

                turn_counts.append(rec.turn_count)
                draw_counts.append(rec.draw_count)
                whot_plays_list.append(rec.whot_plays)
                pick_two_list.append(rec.pick_two_plays)
                pick_three_list.append(rec.pick_three_plays)
                hold_on_list.append(rec.hold_on_plays)
                suspension_list.append(rec.suspensions)
                gen_market_list.append(rec.general_market_activations)
                declaration_violations_list.append(rec.declaration_violations)
                market_reshuffles_list.append(rec.market_reshuffles)
                if rec.truncated:
                    truncation_count += 1

                for st in rec.steps:
                    all_legal_counts.append(st.legal_action_count)
                    hand_sizes_across_steps.append(st.acting_hand_size)

                if (g + 1) % max(1, games_per_cohort // 5) == 0:
                    print(f"    Completed {g + 1}/{games_per_cohort} games")

            cohort_results[cohort_name] = {
                "agent_type": agent_type,
                "games_played": games_per_cohort,
                "turn_count": StatisticalUtilities.calculate_scalar_stats(turn_counts),
                "draw_count": StatisticalUtilities.calculate_scalar_stats(draw_counts),
                "legal_action_count": StatisticalUtilities.calculate_scalar_stats(
                    all_legal_counts
                ),
                "legal_action_ecdf": StatisticalUtilities.compute_ecdf(all_legal_counts),
                "acting_hand_size": StatisticalUtilities.calculate_scalar_stats(
                    hand_sizes_across_steps
                ),
                "special_cards": {
                    "whot": StatisticalUtilities.calculate_scalar_stats(whot_plays_list),
                    "pick_two": StatisticalUtilities.calculate_scalar_stats(pick_two_list),
                    "pick_three": StatisticalUtilities.calculate_scalar_stats(pick_three_list),
                    "hold_on": StatisticalUtilities.calculate_scalar_stats(hold_on_list),
                    "suspension": StatisticalUtilities.calculate_scalar_stats(suspension_list),
                    "general_market": StatisticalUtilities.calculate_scalar_stats(
                        gen_market_list
                    ),
                },
                "declaration_violations": sum(declaration_violations_list),
                "market_reshuffles": sum(market_reshuffles_list),
                "truncation": StatisticalUtilities.wilson_score_interval(
                    truncation_count, games_per_cohort
                ),
            }

    raw_path = writer.filepath

    processed_data = {
        "experiment_id": exp_id,
        "is_pilot": pilot if not dry_run else False,
        "is_dry_run": dry_run,
        "config_hash": config_hash,
        "player_count": player_count,
        "action_space_size": 76,
        "total_deck_size": 54,
        "cohorts": cohort_results,
    }
    processed_path = save_processed_metrics(f"exp01_{suffix}_summary.json", processed_data)

    print(f"\n[EXP-01] Finished successfully.")
    print(f"  Raw data: {raw_path}")
    print(f"  Processed metrics: {processed_path}")

    return processed_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run EXP-01")
    parser.add_argument(
        "--full", action="store_true", help="Run full experiment instead of pilot"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run small dry-run test"
    )
    args = parser.parse_args()
    run_exp01(pilot=not args.full, dry_run=args.dry_run)
