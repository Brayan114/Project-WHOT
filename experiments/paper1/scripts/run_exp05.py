"""EXP-05: Controlled Rule Variants (Stage 3B).

Evaluates derived rule variants against baseline WHOT-NG-v1 using matched seeds:
- VAR-BASE: Baseline WHOT-NG-v1
- VAR-NO-STACK-2: Pick-2 stacking disabled
- VAR-NO-STACK-3: Pick-3 stacking disabled
- VAR-NO-DECL: Last-card declaration disabled
- VAR-PENALTY-2: Last-card violation penalty increased to DRAW_2
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
    TrajectoryCollector,
    compute_config_hash,
    load_experiment_config,
    save_processed_metrics,
    save_raw_telemetry,
)
from whot_ml.environment import GameEnvironment
from whot_ml.ruleset import (
    LastCardViolationPenalty,
    StackingMode,
    WHOTConfig,
    get_baseline_config,
)


def build_variant_config(overrides: Dict[str, Any], player_count: int = 4) -> WHOTConfig:
    """Construct an immutable WHOTConfig with explicit single-factor overrides."""
    kwargs: Dict[str, Any] = {
        "player_count": player_count,
        "ruleset_name": "WHOT-NG-v1",
    }
    for k, v in overrides.items():
        if k in ("pick_two_stacking", "pick_three_stacking"):
            kwargs[k] = StackingMode(v)
        elif k == "last_card_violation_penalty":
            kwargs[k] = LastCardViolationPenalty(v)
        else:
            kwargs[k] = v

    return WHOTConfig(**kwargs)


def run_exp05(pilot: bool = True, dry_run: bool = False) -> Dict[str, Any]:
    """Execute EXP-05 Controlled Rule Variants with matched seeds."""
    config_data = load_experiment_config("exp05_rule_variants.json")
    exp_id = config_data["experiment_id"]
    if dry_run:
        games_per_variant = 2
        suffix = "dry_run"
    else:
        games_per_variant = (
            config_data["pilot_games_per_variant"]
            if pilot
            else config_data["full_games_per_variant"]
        )
        suffix = "pilot" if pilot else "full"

    seed_base = config_data["pilot_seed_base"] if (pilot or dry_run) else config_data["full_seed_base"]
    player_count = config_data["player_count"]
    agent_pop = config_data["agent_population"]

    mode_label = "DRY-RUN" if dry_run else ("PILOT" if pilot else "FULL")
    print(f"\n[EXP-05] Starting Controlled Rule Variants ({mode_label})")
    print(f"  Games per variant: {games_per_variant} (Matched seeds {seed_base}..{seed_base + games_per_variant - 1})")

    all_records: List[GameTrajectoryRecord] = []
    variant_results: Dict[str, Any] = {}
    variant_raw_turns: Dict[str, List[int]] = {}
    variant_raw_draws: Dict[str, List[int]] = {}

    for var in config_data["variants"]:
        var_id = var["variant_id"]
        overrides = var["overrides"]
        desc = var["description"]
        print(f"\n  Evaluating variant: {var_id} — {desc}")

        cfg = build_variant_config(overrides, player_count=player_count)
        cfg_hash = compute_config_hash(cfg)

        turn_counts: List[int] = []
        draw_counts: List[int] = []
        rule_based_wins = 0
        truncations = 0

        for g in range(games_per_variant):
            seed = seed_base + g
            manifest = RunManifest(
                experiment_id=f"{exp_id}-{var_id}",
                is_pilot=pilot if not dry_run else False,
                is_dry_run=dry_run,
                seed=seed,
                player_count=player_count,
                variant_id=var_id,
                ruleset_hash=cfg_hash,
                config_hash=cfg_hash,
                agent_population=agent_pop,
            )

            env = GameEnvironment(config=cfg)
            agents = BalancedSeatAssigner.assign_seats(
                agent_types=agent_pop,
                game_index=g,
                base_seed=seed,
                rotate=False,  # Fixed seating across matched seeds to isolate rule factor
            )

            rec = TrajectoryCollector.play_instrumented_game(
                env=env,
                agents=agents,
                manifest=manifest,
                record_steps=False,
            )
            all_records.append(rec)

            turn_counts.append(rec.turn_count)
            draw_counts.append(rec.draw_count)
            if rec.winner == 0:  # Seat 0 is rule_based
                rule_based_wins += 1
            if rec.truncated:
                truncations += 1

        variant_raw_turns[var_id] = turn_counts
        variant_raw_draws[var_id] = draw_counts

        variant_results[var_id] = {
            "variant_id": var_id,
            "description": desc,
            "config_hash": cfg_hash,
            "games_played": games_per_variant,
            "turn_count": StatisticalUtilities.calculate_scalar_stats(turn_counts),
            "draw_count": StatisticalUtilities.calculate_scalar_stats(draw_counts),
            "rule_based_win_rate": StatisticalUtilities.wilson_score_interval(
                rule_based_wins, games_per_variant
            ),
            "truncation": StatisticalUtilities.wilson_score_interval(
                truncations, games_per_variant
            ),
        }

    # Perform paired statistical comparison relative to VAR-BASE
    base_turns = variant_raw_turns.get("VAR-BASE", [])
    base_draws = variant_raw_draws.get("VAR-BASE", [])
    paired_comparisons: Dict[str, Any] = {}

    for var_id, turns in variant_raw_turns.items():
        if var_id == "VAR-BASE":
            continue
        draws = variant_raw_draws[var_id]
        paired_comparisons[var_id] = {
            "turn_diff_stats": StatisticalUtilities.paired_differences(base_turns, turns),
            "draw_diff_stats": StatisticalUtilities.paired_differences(base_draws, draws),
            "turn_cliffs_delta": StatisticalUtilities.cliffs_delta(turns, base_turns),
            "draw_cliffs_delta": StatisticalUtilities.cliffs_delta(draws, base_draws),
        }

    raw_path = save_raw_telemetry(f"exp05_{suffix}_raw.jsonl", all_records)

    processed_data = {
        "experiment_id": exp_id,
        "is_pilot": pilot if not dry_run else False,
        "is_dry_run": dry_run,
        "variants": variant_results,
        "paired_comparisons_vs_base": paired_comparisons,
    }
    processed_path = save_processed_metrics(f"exp05_{suffix}_summary.json", processed_data)

    print(f"\n[EXP-05] Finished successfully.")
    print(f"  Raw data: {raw_path}")
    print(f"  Processed metrics: {processed_path}")

    return processed_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run EXP-05")
    parser.add_argument(
        "--full", action="store_true", help="Run full experiment instead of pilot"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run small dry-run test"
    )
    args = parser.parse_args()
    run_exp05(pilot=not args.full, dry_run=args.dry_run)
