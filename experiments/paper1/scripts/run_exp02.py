"""EXP-02: Partial Observability Demonstration (Stage 3B).

Rigorously demonstrates that distinct complete world states S_a != S_b map to identical
player observations Omega_p(S_a) == Omega_p(S_b), verifies zero information leakage,
and measures trajectory divergence rates under controlled rollouts.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.paper1.scripts.common import (
    BalancedSeatAssigner,
    ExperimentPaths,
    RunManifest,
    StatisticalUtilities,
    compute_config_hash,
    load_experiment_config,
    save_processed_metrics,
)
from whot_ml.card import Card
from whot_ml.environment import GameEnvironment
from whot_ml.event import Event
from whot_ml.ruleset import WHOTConfig, get_baseline_config
from whot_ml.serializer import restore_state, serialize_state
from whot_ml.state import GameState


def compute_log_combinatorial_uncertainty(
    unseen_cards_count: int, opponent_hand_sizes: List[int]
) -> float:
    """Compute log10 of compatible hidden state partitions: log10(U! / prod(h_j!))."""
    if unseen_cards_count < 0:
        return 0.0

    log_u_fact = sum(math.log10(i) for i in range(1, unseen_cards_count + 1))
    log_h_fact = sum(
        sum(math.log10(i) for i in range(1, h + 1))
        for h in opponent_hand_sizes
        if h > 0
    )
    return round(log_u_fact - log_h_fact, 4)


def construct_equivalent_states(
    env: GameEnvironment,
    observing_player: int,
) -> List[Dict[str, Any]]:
    """Construct observationally equivalent state variations S_b from current state S_a.

    Generates three controlled permutations:
    1. Opponent-Opponent card swap (Mode A)
    2. Market sequence reversal (Mode B)
    3. Opponent-Market card swap (Mode C)
    """
    state_a = env.get_full_state()
    obs_a = env.observe(observing_player)
    obs_a_dict = obs_a.to_dict()

    hist_dicts = [e.to_dict() for e in env.history]
    candidates: List[Dict[str, Any]] = []
    p_count = state_a.config.player_count
    opponents = [p for p in range(p_count) if p != observing_player]

    # --- Mode A: Swap cards between two opponents ---
    if len(opponents) >= 2:
        p1, p2 = opponents[0], opponents[1]
        h1 = list(state_a.hands[p1])
        h2 = list(state_a.hands[p2])
        if h1 and h2 and h1[0].id != h2[0].id:
            dict_b = serialize_state(state_a)
            # Swap first card of p1 and p2 in serialized state
            dict_b["hands"][str(p1)][0], dict_b["hands"][str(p2)][0] = (
                dict_b["hands"][str(p2)][0],
                dict_b["hands"][str(p1)][0],
            )
            candidates.append({
                "mode": "OPPONENT_SWAP",
                "serialized_state_b": dict_b,
                "history": hist_dicts,
                "diff_description": f"Swapped card {h1[0].id} (Opponent {p1}) with {h2[0].id} (Opponent {p2})",
            })

    # --- Mode B: Reverse the internal order of the market ---
    if len(state_a.market) >= 2:
        dict_b = serialize_state(state_a)
        dict_b["market"].reverse()
        candidates.append({
            "mode": "MARKET_REVERSAL",
            "serialized_state_b": dict_b,
            "history": hist_dicts,
            "diff_description": f"Reversed internal order of {len(state_a.market)} draw-market cards",
        })

    # --- Mode C: Swap a card between opponent and market ---
    if opponents and state_a.market:
        p1 = opponents[0]
        h1 = list(state_a.hands[p1])
        if h1:
            dict_b = serialize_state(state_a)
            dict_b["hands"][str(p1)][0], dict_b["market"][0] = (
                dict_b["market"][0],
                dict_b["hands"][str(p1)][0],
            )
            candidates.append({
                "mode": "OPPONENT_MARKET_SWAP",
                "serialized_state_b": dict_b,
                "history": hist_dicts,
                "diff_description": f"Swapped card {h1[0].id} (Opponent {p1}) with {state_a.market[0].id} (Market)",
            })

    return candidates


def run_controlled_rollout(
    state_a_dict: Dict[str, Any],
    state_b_dict: Dict[str, Any],
    history_dicts: Optional[List[Dict[str, Any]]] = None,
    rollout_steps: int = 20,
    rollout_seed: int = 42,
) -> Dict[str, Any]:
    """Execute deterministically seeded rollouts from S_a and S_b to measure divergence."""
    cfg = WHOTConfig(player_count=len(state_a_dict["hands"]))

    env_a = GameEnvironment(config=cfg)
    env_a.restore_state(state_a_dict)
    if history_dicts:
        env_a.history = [Event.from_dict(d) for d in history_dicts]

    env_b = GameEnvironment(config=cfg)
    env_b.restore_state(state_b_dict)
    if history_dicts:
        env_b.history = [Event.from_dict(d) for d in history_dicts]

    agents_a = BalancedSeatAssigner.assign_seats(
        agent_types=["rule_based"] * cfg.player_count,
        game_index=0,
        base_seed=rollout_seed,
        rotate=False,
    )
    agents_b = BalancedSeatAssigner.assign_seats(
        agent_types=["rule_based"] * cfg.player_count,
        game_index=0,
        base_seed=rollout_seed,
        rotate=False,
    )

    diverged = False
    divergence_step: Optional[int] = None
    divergence_detail: Optional[str] = None

    for step in range(rollout_steps):
        if env_a.is_terminal or env_b.is_terminal:
            break

        curr_a = env_a.current_player
        curr_b = env_b.current_player

        if curr_a != curr_b:
            diverged = True
            divergence_step = step
            divergence_detail = f"Current player diverged: P{curr_a} vs P{curr_b}"
            break

        obs_a = env_a.observe(curr_a)
        obs_b = env_b.observe(curr_b)

        act_a = agents_a[curr_a].act(obs_a)
        act_b = agents_b[curr_b].act(obs_b)

        if act_a.action_type != act_b.action_type or act_a.card_id != act_b.card_id:
            diverged = True
            divergence_step = step
            divergence_detail = f"Action diverged at step {step}: {act_a} vs {act_b}"
            break

        res_a = env_a.step(act_a, acting_player=curr_a)
        res_b = env_b.step(act_b, acting_player=curr_b)

        # Check if events diverged
        events_a = [e.event_type.value for e in res_a.info.get("events", [])]
        events_b = [e.event_type.value for e in res_b.info.get("events", [])]
        if events_a != events_b:
            diverged = True
            divergence_step = step
            divergence_detail = f"Events diverged at step {step}: {events_a} vs {events_b}"
            break

    return {
        "diverged": diverged,
        "divergence_step": divergence_step,
        "divergence_detail": divergence_detail,
        "steps_simulated": step + 1 if not env_a.is_terminal else step,
    }


def run_exp02(pilot: bool = True, dry_run: bool = False) -> Dict[str, Any]:
    """Execute EXP-02 Partial Observability Demonstration."""
    config_data = load_experiment_config("exp02_partial_observability.json")
    exp_id = config_data["experiment_id"]
    if dry_run:
        source_games = 5
        suffix = "dry_run"
    else:
        source_games = (
            config_data["pilot_source_games"] if pilot else config_data["full_source_games"]
        )
        suffix = "pilot" if pilot else "full"

    seed_base = config_data["pilot_seed_base"] if (pilot or dry_run) else config_data["full_seed_base"]
    player_count = config_data["player_count"]
    obs_player = config_data["observing_player"]
    stages = config_data["stages"]
    rollout_max_steps = config_data["rollout_max_steps"]
    rollout_seed = config_data["rollout_seed"]

    whot_config = WHOTConfig(player_count=player_count)
    config_hash = compute_config_hash(whot_config)

    mode_label = "DRY-RUN" if dry_run else ("PILOT" if pilot else "FULL")
    print(
        f"\n[EXP-02] Starting Partial Observability Demonstration ({mode_label})"
    )
    print(f"  Source games: {source_games} | Observing player: {obs_player}")

    evaluated_pairs: List[Dict[str, Any]] = []
    log_uncertainties: List[float] = []
    divergence_steps: List[int] = []
    mode_counts: Dict[str, int] = {}
    mode_divergence_counts: Dict[str, int] = {}

    total_pairs_tested = 0
    equivalent_pairs_verified = 0
    leak_free_pairs_verified = 0
    divergent_pairs_count = 0
    representative_examples: List[Dict[str, Any]] = []

    for g in range(source_games):
        seed = seed_base + g
        env = GameEnvironment(config=whot_config)
        agents = BalancedSeatAssigner.assign_seats(
            agent_types=["rule_based"] * player_count,
            game_index=g,
            base_seed=seed,
            rotate=False,
        )
        env.reset(seed=seed)

        current_step = 0
        target_steps = {stg["timestep"]: stg["name"] for stg in stages}
        max_target = max(target_steps.keys())

        while not env.is_terminal and current_step <= max_target:
            if current_step in target_steps:
                stage_name = target_steps[current_step]
                state_a = env.get_full_state()
                obs_a = env.observe(obs_player)
                obs_a_dict = obs_a.to_dict()

                # Combinatorial uncertainty
                opp_sizes = [len(state_a.hands[p]) for p in range(player_count) if p != obs_player]
                unseen = 54 - len(state_a.hands[obs_player]) - len(state_a.play_pile)
                log_u = compute_log_combinatorial_uncertainty(unseen, opp_sizes)
                log_uncertainties.append(log_u)

                # Generate candidates
                candidates = construct_equivalent_states(env, obs_player)

                for cand in candidates:
                    total_pairs_tested += 1
                    mode = cand["mode"]
                    mode_counts[mode] = mode_counts.get(mode, 0) + 1

                    state_b_dict = cand["serialized_state_b"]
                    state_a_dict = serialize_state(state_a)

                    # 1. Verify S_a != S_b
                    state_differs = state_a_dict != state_b_dict

                    # 2. Re-create env for S_b and observe player
                    env_b = GameEnvironment(config=whot_config)
                    env_b.restore_state(state_b_dict)
                    env_b.history = [Event.from_dict(d) for d in cand["history"]]
                    obs_b = env_b.observe(obs_player)
                    obs_b_dict = obs_b.to_dict()

                    # Verify Omega_p(S_a) == Omega_p(S_b)
                    obs_equal = obs_a_dict == obs_b_dict
                    if obs_equal and state_differs:
                        equivalent_pairs_verified += 1

                    # 3. Verify zero information leakage
                    # Check that no hidden opponent cards appear in obs_a or obs_b
                    hidden_card_ids = set()
                    for p in range(player_count):
                        if p != obs_player:
                            hidden_card_ids.update(c.id for c in state_a.hands[p])
                    hidden_in_obs = any(cid in obs_a_dict["hand"] for cid in hidden_card_ids)
                    if not hidden_in_obs:
                        leak_free_pairs_verified += 1

                    # 4. Rollout and measure divergence
                    rollout_res = run_controlled_rollout(
                        state_a_dict=state_a_dict,
                        state_b_dict=state_b_dict,
                        history_dicts=cand["history"],
                        rollout_steps=rollout_max_steps,
                        rollout_seed=rollout_seed,
                    )

                    if rollout_res["diverged"]:
                        divergent_pairs_count += 1
                        mode_divergence_counts[mode] = mode_divergence_counts.get(mode, 0) + 1
                        if rollout_res["divergence_step"] is not None:
                            divergence_steps.append(rollout_res["divergence_step"])

                    pair_summary = {
                        "source_game_seed": seed,
                        "timestep": current_step,
                        "stage": stage_name,
                        "mode": mode,
                        "description": cand["diff_description"],
                        "log_uncertainty": log_u,
                        "s_a_differs_s_b": state_differs,
                        "obs_a_equals_obs_b": obs_equal,
                        "leak_free": not hidden_in_obs,
                        "rollout": rollout_res,
                    }
                    evaluated_pairs.append(pair_summary)

                    # Save up to 3 concrete representative examples for paper inclusion
                    if len(representative_examples) < 3 and obs_equal and rollout_res["diverged"]:
                        representative_examples.append({
                            "source_seed": seed,
                            "step": current_step,
                            "mode": mode,
                            "description": cand["diff_description"],
                            "observed_hand": [c.id for c in obs_a.hand],
                            "top_card": obs_a.top_card.id,
                            "current_call": obs_a.current_call.value,
                            "divergence_step": rollout_res["divergence_step"],
                            "divergence_detail": rollout_res["divergence_detail"],
                        })

            # Advance game
            curr = env.current_player
            obs = env.observe(curr)
            act = agents[curr].act(obs)
            env.step(act, acting_player=curr)
            current_step += 1

    # Save raw pairs JSON
    ExperimentPaths.ensure_directories()
    raw_path = ExperimentPaths.RAW / f"exp02_{suffix}_pairs.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(evaluated_pairs, f, indent=2)

    # Processed summary
    div_rate = divergent_pairs_count / total_pairs_tested if total_pairs_tested > 0 else 0.0
    processed_data = {
        "experiment_id": exp_id,
        "is_pilot": pilot if not dry_run else False,
        "is_dry_run": dry_run,
        "total_pairs_tested": total_pairs_tested,
        "equivalence_verification_rate": (
            equivalent_pairs_verified / total_pairs_tested if total_pairs_tested > 0 else 1.0
        ),
        "information_leak_rate": (
            1.0 - (leak_free_pairs_verified / total_pairs_tested) if total_pairs_tested > 0 else 0.0
        ),
        "overall_divergence_rate": round(div_rate, 4),
        "mode_counts": mode_counts,
        "mode_divergence_counts": mode_divergence_counts,
        "mode_divergence_rates": {
            m: round(mode_divergence_counts.get(m, 0) / count, 4)
            for m, count in mode_counts.items()
        },
        "log_uncertainty_stats": StatisticalUtilities.calculate_scalar_stats(log_uncertainties),
        "divergence_step_stats": StatisticalUtilities.calculate_scalar_stats(divergence_steps),
        "representative_examples": representative_examples,
    }

    processed_path = save_processed_metrics(f"exp02_{suffix}_summary.json", processed_data)

    print(f"\n[EXP-02] Finished successfully.")
    print(f"  Pairs evaluated: {total_pairs_tested}")
    print(f"  Equivalence rate: {processed_data['equivalence_verification_rate']:.1%}")
    print(f"  Information leak rate: {processed_data['information_leak_rate']:.1%}")
    print(f"  Trajectory divergence rate: {processed_data['overall_divergence_rate']:.1%}")
    print(f"  Raw data: {raw_path}")
    print(f"  Processed metrics: {processed_path}")

    return processed_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run EXP-02")
    parser.add_argument(
        "--full", action="store_true", help="Run full experiment instead of pilot"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run small dry-run test"
    )
    args = parser.parse_args()
    run_exp02(pilot=not args.full, dry_run=args.dry_run)
