"""EXP-03: Baseline Agent Characterization (Stage 3B).

Evaluates RandomLegalAgent vs RuleBasedAgent across controlled cohorts:
- RRRR (4 RandomLegalAgent)
- BBBB (4 RuleBasedAgent)
- BRRR (1 RuleBasedAgent vs 3 RandomLegalAgent with balanced seat rotation)
- BR_2P (2-player head-to-head with alternating seating)
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
from whot_ml.ruleset import WHOTConfig, get_baseline_config


def run_exp03(pilot: bool = True, dry_run: bool = False) -> Dict[str, Any]:
    """Execute EXP-03 Baseline Agent Characterization."""
    config_data = load_experiment_config("exp03_baselines.json")
    exp_id = config_data["experiment_id"]
    suffix = "dry_run" if dry_run else ("pilot" if pilot else "full")
    seed_base = config_data["pilot_seed_base"] if (pilot or dry_run) else config_data["full_seed_base"]

    mode_label = "DRY-RUN" if dry_run else ("PILOT" if pilot else "FULL")
    print(f"\n[EXP-03] Starting Baseline Agent Characterization ({mode_label})")

    all_records: List[GameTrajectoryRecord] = []
    matchup_summaries: Dict[str, Any] = {}

    for matchup in config_data["matchups"]:
        m_id = matchup["matchup_id"]
        p_count = matchup["player_count"]
        agent_list = matchup["agents"]
        seat_rot = matchup.get("seat_rotation", False)
        target_agent = matchup.get("target_agent_type", None)

        if dry_run:
            num_games = 4 if seat_rot else 2
        else:
            num_games = matchup["pilot_games"] if pilot else matchup["full_games"]
        whot_config = WHOTConfig(player_count=p_count)
        cfg_hash = compute_config_hash(whot_config)

        print(f"\n  Running Matchup: {m_id} ({num_games} games | {p_count} players)")

        wins_by_seat: Dict[int, int] = {p: 0 for p in range(p_count)}
        wins_by_agent_type: Dict[str, int] = {}
        games_by_agent_type: Dict[str, int] = {}
        finishing_ranks_by_agent_type: Dict[str, List[float]] = {}
        turn_lengths: List[int] = []
        draw_counts: List[int] = []
        truncations = 0
        declaration_violations_by_agent: Dict[str, int] = {}

        for g in range(num_games):
            seed = seed_base + g
            agents = BalancedSeatAssigner.assign_seats(
                agent_types=agent_list,
                game_index=g,
                base_seed=seed,
                rotate=seat_rot,
            )

            manifest = RunManifest(
                experiment_id=f"{exp_id}-{m_id}",
                is_pilot=pilot if not dry_run else False,
                is_dry_run=dry_run,
                seed=seed,
                player_count=p_count,
                ruleset_hash=cfg_hash,
                config_hash=cfg_hash,
                agent_population=[a.name for a in agents.values()],
            )

            env = GameEnvironment(config=whot_config)
            rec = TrajectoryCollector.play_instrumented_game(
                env=env,
                agents=agents,
                manifest=manifest,
                record_steps=False,  # Summary-level recording sufficient for tournament
            )
            all_records.append(rec)

            turn_lengths.append(rec.turn_count)
            draw_counts.append(rec.draw_count)
            if rec.truncated:
                truncations += 1

            # Count games played per agent type
            for p, ag in agents.items():
                atype = "rule_based" if "RuleBased" in ag.name else "random"
                games_by_agent_type[atype] = games_by_agent_type.get(atype, 0) + 1

            if rec.winner is not None:
                winner_seat = rec.winner
                wins_by_seat[winner_seat] += 1
                winner_agent = agents[winner_seat]
                w_type = "rule_based" if "RuleBased" in winner_agent.name else "random"
                wins_by_agent_type[w_type] = wins_by_agent_type.get(w_type, 0) + 1

            # Compute ranks from final hand sizes
            sorted_players = sorted(
                rec.final_hand_sizes.keys(), key=lambda p: rec.final_hand_sizes[p]
            )
            for rank_idx, p in enumerate(sorted_players):
                ag = agents[p]
                atype = "rule_based" if "RuleBased" in ag.name else "random"
                if atype not in finishing_ranks_by_agent_type:
                    finishing_ranks_by_agent_type[atype] = []
                finishing_ranks_by_agent_type[atype].append(rank_idx + 1)

            if (g + 1) % max(1, num_games // 4) == 0:
                print(f"    Completed {g + 1}/{num_games} games")

        # Win rates with Wilson score CIs
        win_rate_stats = {}
        for atype, total_g in games_by_agent_type.items():
            wins = wins_by_agent_type.get(atype, 0)
            win_rate_stats[atype] = StatisticalUtilities.wilson_score_interval(wins, total_g)

        rank_stats = {
            atype: StatisticalUtilities.calculate_scalar_stats(ranks)
            for atype, ranks in finishing_ranks_by_agent_type.items()
        }

        matchup_summaries[m_id] = {
            "player_count": p_count,
            "games_played": num_games,
            "wins_by_seat": wins_by_seat,
            "wins_by_agent_type": wins_by_agent_type,
            "win_rate_stats": win_rate_stats,
            "rank_stats": rank_stats,
            "turn_length": StatisticalUtilities.calculate_scalar_stats(turn_lengths),
            "draw_count": StatisticalUtilities.calculate_scalar_stats(draw_counts),
            "truncation": StatisticalUtilities.wilson_score_interval(truncations, num_games),
        }

    # Save raw and processed outputs
    raw_path = save_raw_telemetry(f"exp03_{suffix}_raw.jsonl", all_records)

    processed_data = {
        "experiment_id": exp_id,
        "is_pilot": pilot if not dry_run else False,
        "is_dry_run": dry_run,
        "matchups": matchup_summaries,
    }
    processed_path = save_processed_metrics(f"exp03_{suffix}_summary.json", processed_data)

    print(f"\n[EXP-03] Finished successfully.")
    print(f"  Raw data: {raw_path}")
    print(f"  Processed metrics: {processed_path}")

    return processed_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run EXP-03")
    parser.add_argument(
        "--full", action="store_true", help="Run full experiment instead of pilot"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run small dry-run test"
    )
    args = parser.parse_args()
    run_exp03(pilot=not args.full, dry_run=args.dry_run)
