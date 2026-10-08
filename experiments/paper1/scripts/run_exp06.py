"""EXP-06: Determinism and Reproducibility (Stage 3B).

Evaluates bitwise event-level determinism:
- Sub-Protocol 6A: Independent Replay Parity (Same seed -> Identical event hash)
- Sub-Protocol 6B: Mid-Game Checkpoint Restoration Parity (Uninterrupted vs Restored continuation)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.paper1.scripts.common import (
    BalancedSeatAssigner,
    ExperimentPaths,
    RunManifest,
    compute_config_hash,
    load_experiment_config,
    save_processed_metrics,
)
from whot_ml.environment import EnvStepResult, GameEnvironment
from whot_ml.ruleset import WHOTConfig, get_baseline_config
from whot_ml.serializer import restore_state, serialize_state


def execute_trajectory_trace(
    env: GameEnvironment,
    agents: Dict[int, Any],
    seed: int,
    max_steps: int = 500,
) -> Dict[str, Any]:
    """Execute episode and record full event-level trace with SHA-256 digest."""
    env.reset(seed=seed)
    for p, ag in agents.items():
        ag.reset(player_id=p, seed=seed + p)

    events_trace: List[Dict[str, Any]] = []
    actions_trace: List[str] = []
    rewards_trace: List[Dict[int, float]] = []

    step = 0
    while not env.is_terminal and step < max_steps:
        curr = env.current_player
        obs = env.observe(curr)
        action = agents[curr].act(obs)
        actions_trace.append(str(action))

        step_res: EnvStepResult = env.step(action, acting_player=curr)
        step_events = [e.to_dict() for e in step_res.info.get("events", [])]
        events_trace.extend(step_events)
        rewards_trace.append({p: float(r) for p, r in step_res.rewards.items()})
        step += 1

    digest_input = {
        "actions": actions_trace,
        "events": events_trace,
        "rewards": rewards_trace,
        "winner": env.winner,
        "is_terminal": env.is_terminal,
    }
    serialized = json.dumps(digest_input, sort_keys=True)
    sha256 = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    return {
        "sha256": sha256,
        "total_steps": step,
        "winner": env.winner,
        "actions": actions_trace,
        "events": events_trace,
    }


import copy


def execute_checkpoint_test(
    seed: int,
    checkpoint_step: int = 10,
    player_count: int = 4,
) -> Tuple[bool, str]:
    """Test mid-game serialization and restoration continuation equivalence."""
    cfg = WHOTConfig(player_count=player_count)

    # --- Run A: Uninterrupted Run ---
    env_a = GameEnvironment(config=cfg)
    agents_a = BalancedSeatAssigner.assign_seats(
        agent_types=["random"] * player_count,
        game_index=0,
        base_seed=seed,
        rotate=False,
    )
    env_a.reset(seed=seed)
    for p, ag in agents_a.items():
        ag.reset(player_id=p, seed=seed + p)

    actions_uninterrupted: List[str] = []
    events_uninterrupted: List[str] = []

    # Advance Run A to checkpoint step
    for _ in range(checkpoint_step):
        if env_a.is_terminal:
            break
        curr = env_a.current_player
        obs = env_a.observe(curr)
        act = agents_a[curr].act(obs)
        res = env_a.step(act, acting_player=curr)

    # Checkpoint state and preserve identical agent RNG state at checkpoint
    serialized_checkpoint = serialize_state(env_a.get_full_state())
    agents_b = copy.deepcopy(agents_a)

    # Continue Run A to terminal
    while not env_a.is_terminal:
        curr = env_a.current_player
        obs = env_a.observe(curr)
        act = agents_a[curr].act(obs)
        actions_uninterrupted.append(str(act))
        res = env_a.step(act, acting_player=curr)
        for e in res.info.get("events", []):
            events_uninterrupted.append(e.event_type.value)

    # --- Run B: Restored from Checkpoint ---
    env_b = GameEnvironment(config=cfg)
    env_b.restore_state(serialized_checkpoint)

    actions_restored: List[str] = []
    events_restored: List[str] = []

    while not env_b.is_terminal:
        curr = env_b.current_player
        obs = env_b.observe(curr)
        act = agents_b[curr].act(obs)
        actions_restored.append(str(act))
        res = env_b.step(act, acting_player=curr)
        for e in res.info.get("events", []):
            events_restored.append(e.event_type.value)

    # Compare continuation traces
    actions_match = actions_uninterrupted == actions_restored
    events_match = events_uninterrupted == events_restored
    winner_match = env_a.winner == env_b.winner

    if actions_match and events_match and winner_match:
        return True, "Exact continuation match"
    else:
        diff = []
        if not actions_match:
            diff.append(f"Actions mismatch (len {len(actions_uninterrupted)} vs {len(actions_restored)})")
        if not events_match:
            diff.append("Events mismatch")
        if not winner_match:
            diff.append(f"Winner mismatch ({env_a.winner} vs {env_b.winner})")
        return False, "; ".join(diff)


def run_exp06(pilot: bool = True, dry_run: bool = False) -> Dict[str, Any]:
    """Execute EXP-06 Determinism and Reproducibility."""
    config_data = load_experiment_config("exp06_determinism.json")
    exp_id = config_data["experiment_id"]
    if dry_run:
        num_games = 5
        suffix = "dry_run"
    else:
        num_games = (
            config_data["pilot_games"] if pilot else config_data["full_games"]
        )
        suffix = "pilot" if pilot else "full"

    seed_base = config_data["pilot_seed_base"] if (pilot or dry_run) else config_data["full_seed_base"]
    player_count = config_data["player_count"]
    checkpoint_step = config_data["checkpoint_step"]
    agent_pop = config_data["agent_population"]

    whot_config = WHOTConfig(player_count=player_count)

    mode_label = "DRY-RUN" if dry_run else ("PILOT" if pilot else "FULL")
    print(f"\n[EXP-06] Starting Determinism and Reproducibility ({mode_label})")
    print(f"  Tests to execute: {num_games} replays + {num_games} checkpoint restorations")

    # Sub-Protocol 6A: Independent Replays
    print("\n  Executing Sub-Protocol 6A (Independent Replays)...")
    replay_matches = 0
    replay_results: List[Dict[str, Any]] = []

    for g in range(num_games):
        seed = seed_base + g
        env1 = GameEnvironment(config=whot_config)
        agents1 = BalancedSeatAssigner.assign_seats(agent_pop, game_index=g, base_seed=seed, rotate=False)
        trace1 = execute_trajectory_trace(env1, agents1, seed)

        env2 = GameEnvironment(config=whot_config)
        agents2 = BalancedSeatAssigner.assign_seats(agent_pop, game_index=g, base_seed=seed, rotate=False)
        trace2 = execute_trajectory_trace(env2, agents2, seed)

        is_identical = trace1["sha256"] == trace2["sha256"]
        if is_identical:
            replay_matches += 1

        replay_results.append({
            "seed": seed,
            "hash1": trace1["sha256"],
            "hash2": trace2["sha256"],
            "identical": is_identical,
        })

    # Sub-Protocol 6B: Checkpoint Restoration
    print("  Executing Sub-Protocol 6B (Checkpoint Restoration)...")
    checkpoint_matches = 0
    checkpoint_results: List[Dict[str, Any]] = []

    for g in range(num_games):
        seed = seed_base + 1000 + g
        success, detail = execute_checkpoint_test(seed, checkpoint_step=checkpoint_step, player_count=player_count)
        if success:
            checkpoint_matches += 1
        checkpoint_results.append({
            "seed": seed,
            "success": success,
            "detail": detail,
        })

    total_tests = num_games * 2
    total_passed = replay_matches + checkpoint_matches
    rsr = (total_passed / total_tests) * 100.0

    raw_data = {
        "replays": replay_results,
        "checkpoints": checkpoint_results,
    }
    ExperimentPaths.ensure_directories()
    raw_path = ExperimentPaths.RAW / f"exp06_{suffix}_raw.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, indent=2)

    processed_data = {
        "experiment_id": exp_id,
        "is_pilot": pilot if not dry_run else False,
        "is_dry_run": dry_run,
        "replays_tested": num_games,
        "replays_matched": replay_matches,
        "replay_success_rate": replay_matches / num_games if num_games > 0 else 0.0,
        "checkpoints_tested": num_games,
        "checkpoints_matched": checkpoint_matches,
        "checkpoint_success_rate": checkpoint_matches / num_games if num_games > 0 else 0.0,
        "total_tests": total_tests,
        "total_passed": total_passed,
        "reproduction_success_rate_percent": round(rsr, 2),
    }
    processed_path = save_processed_metrics(f"exp06_{suffix}_summary.json", processed_data)

    print(f"\n[EXP-06] Finished successfully.")
    print(f"  Replays Matched: {replay_matches}/{num_games}")
    print(f"  Checkpoints Matched: {checkpoint_matches}/{num_games}")
    print(f"  Reproduction Success Rate: {rsr:.2f}%")
    print(f"  Raw data: {raw_path}")
    print(f"  Processed metrics: {processed_path}")

    return processed_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run EXP-06")
    parser.add_argument(
        "--full", action="store_true", help="Run full experiment instead of pilot"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run small dry-run test"
    )
    args = parser.parse_args()
    run_exp06(pilot=not args.full, dry_run=args.dry_run)
