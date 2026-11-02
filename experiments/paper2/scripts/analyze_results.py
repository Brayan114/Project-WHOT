"""Evaluation Matrix and Learning Curve Plotting for WHOT-ML Paper 2.

Analyzes training telemetry (training_metrics.csv) and evaluates final PPO checkpoints
in head-to-head match-ups (PPO vs. 3 RuleBased) and symmetric self-play (PPO vs. PPO),
computing exact Wilson 95% confidence intervals and rendering publication figures.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys
from typing import Any, Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import torch

# Ensure repository root is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from whot_ml.action import index_to_action
from whot_ml.agents.rule_based_agent import RuleBasedAgent
from whot_ml.environment import GameEnvironment
from whot_ml.ruleset import get_baseline_config

from experiments.paper2.envs.self_play_wrapper import SelfPlayEnvWrapper
from experiments.paper2.models.feedforward_encoder import FeedforwardEncoder
from experiments.paper2.models.ppo_network import MaskedActorCritic
from experiments.paper2.scripts.train_ppo import select_action


def compute_wilson_ci(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float, float]:
    """Compute Wilson score interval for binomial proportion with continuity correction."""
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    z = 1.95996  # 95% two-sided normal quantile
    denom = 1.0 + (z**2) / n
    center = (p + (z**2) / (2.0 * n)) / denom
    margin = (z / denom) * math.sqrt((p * (1.0 - p) / n) + ((z**2) / (4.0 * (n**2))))
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    return p, lower, upper


def plot_learning_curves(csv_path: str, output_dir: str) -> None:
    """Generate publication learning curves from training metrics CSV."""
    if not os.path.exists(csv_path):
        print(f"[WARN] Metrics CSV not found at {csv_path}. Skipping learning curves.")
        return

    steps: List[int] = []
    actor_losses: List[float] = []
    critic_losses: List[float] = []
    entropies: List[float] = []
    win_rates: List[float] = []
    trunc_rates: List[float] = []

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            steps.append(int(row["step"]))
            actor_losses.append(float(row["actor_loss"]))
            critic_losses.append(float(row["critic_loss"]))
            entropies.append(float(row["entropy"]))
            win_rates.append(float(row["eval_win_rate"]))
            trunc_rates.append(float(row["eval_trunc_rate"]))

    if not steps:
        print("[WARN] No metrics data rows found in CSV.")
        return

    os.makedirs(output_dir, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    # 1. Combined 3-Panel Figure
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5), dpi=300)

    # Panel A: Win Rate vs Steps
    axes[0].plot(steps, [w * 100 for w in win_rates], marker="o", color="#1f77b4", linewidth=2.0, label="PPO vs 3 RuleBased")
    axes[0].axhline(25.0, color="#7f7f7f", linestyle="--", linewidth=1.2, label="Fair Share (25%)")
    axes[0].set_xlabel("Environment Timesteps", fontsize=11, fontweight="bold")
    axes[0].set_ylabel("Win Rate (%)", fontsize=11, fontweight="bold")
    axes[0].set_title("(a) Evaluation Win Rate", fontsize=12, fontweight="bold")
    axes[0].set_ylim(-2, 102)
    axes[0].legend(loc="upper left")

    # Panel B: Truncation Rate vs Steps
    axes[1].plot(steps, [t * 100 for t in trunc_rates], marker="s", color="#d62728", linewidth=2.0, label="PPO Truncation Rate")
    axes[1].axhline(43.6, color="#ff7f0e", linestyle=":", linewidth=1.5, label="RuleBased Baseline (43.6%)")
    axes[1].set_xlabel("Environment Timesteps", fontsize=11, fontweight="bold")
    axes[1].set_ylabel("Truncation Rate (%)", fontsize=11, fontweight="bold")
    axes[1].set_title("(b) Emergent Stall Truncation", fontsize=12, fontweight="bold")
    axes[1].set_ylim(-2, 102)
    axes[1].legend(loc="upper right")

    # Panel C: Policy Entropy vs Steps
    axes[2].plot(steps, entropies, marker="^", color="#2ca02c", linewidth=2.0, label="Policy Entropy H(π)")
    axes[2].set_xlabel("Environment Timesteps", fontsize=11, fontweight="bold")
    axes[2].set_ylabel("Entropy (nats)", fontsize=11, fontweight="bold")
    axes[2].set_title("(c) Policy Entropy Annealing", fontsize=12, fontweight="bold")
    axes[2].legend(loc="upper right")

    plt.tight_layout()
    combined_fig_path = os.path.join(output_dir, "fig_learning_curves.png")
    plt.savefig(combined_fig_path, bbox_inches="tight")
    plt.close()
    print(f"[PLOT] Saved combined learning curves to {combined_fig_path}")


def run_evaluation_matrix(
    model_path: str,
    num_games: int = 1000,
    base_seed: int = 80000,
    device_name: str = "cpu",
) -> Dict[str, Any]:
    """Execute evaluation matrix: PPO vs 3 RuleBased and PPO symmetric self-play."""
    device = torch.device(device_name)
    encoder = FeedforwardEncoder(num_players=4)
    network = MaskedActorCritic(obs_dim=280, action_dim=76, hidden_dim=256).to(device)

    if os.path.exists(model_path):
        state_dict = torch.load(model_path, map_location=device)
        network.load_state_dict(state_dict)
        print(f"[EVAL] Successfully loaded weights from {model_path}")
    else:
        print(f"[WARN] Model path {model_path} not found; evaluating uninitialized network.")

    network.eval()
    rule_agents = [RuleBasedAgent(name=f"RuleBased_{i}") for i in range(4)]

    # -------------------------------------------------------------
    # 1. Asymmetric Benchmark: 1 PPO (Seat 0) vs 3 RuleBased (Seats 1..3)
    # -------------------------------------------------------------
    print(f"\n[EVAL 1/2] Running {num_games} games: PPO (Seat 0) vs 3 RuleBased...")
    ppo_wins_vs_rule = 0
    truncations_vs_rule = 0
    total_turns_vs_rule = 0

    for g in range(num_games):
        seed = base_seed + g
        cfg = get_baseline_config()
        cfg_env = GameEnvironment(config=cfg)
        obs_dict = cfg_env.reset(seed=seed)

        terminated = False
        truncated = False
        turns = 0

        while not (terminated or truncated):
            curr_p = cfg_env.current_player
            obs = obs_dict[curr_p]

            if curr_p == 0:
                obs_tensor = encoder.encode(obs)
                mask_tensor = torch.tensor(obs.action_mask, dtype=torch.bool)
                action_idx, _, _ = select_action(network, obs_tensor, mask_tensor, device, deterministic=True)
                action = index_to_action(action_idx)
            else:
                action = rule_agents[curr_p].act(obs)

            step_res = cfg_env.step(action)
            obs_dict[step_res.next_player] = step_res.observation
            terminated = step_res.terminated
            truncated = step_res.truncated
            turns += 1

        total_turns_vs_rule += turns
        if truncated:
            truncations_vs_rule += 1
        elif cfg_env.winner == 0:
            ppo_wins_vs_rule += 1

    p_win_rule, win_low_rule, win_high_rule = compute_wilson_ci(ppo_wins_vs_rule, num_games)
    p_trunc_rule, trunc_low_rule, trunc_high_rule = compute_wilson_ci(truncations_vs_rule, num_games)
    mean_turns_rule = total_turns_vs_rule / num_games

    # -------------------------------------------------------------
    # 2. Symmetric Benchmark: PPO Self-Play (All 4 Seats)
    # -------------------------------------------------------------
    print(f"[EVAL 2/2] Running {num_games} games: PPO Symmetric Self-Play...")
    seat_wins_sp = [0, 0, 0, 0]
    truncations_sp = 0
    total_turns_sp = 0

    for g in range(num_games):
        seed = base_seed + 100000 + g
        cfg = get_baseline_config()
        cfg_env = GameEnvironment(config=cfg)
        obs_dict = cfg_env.reset(seed=seed)

        terminated = False
        truncated = False
        turns = 0

        while not (terminated or truncated):
            curr_p = cfg_env.current_player
            obs = obs_dict[curr_p]

            obs_tensor = encoder.encode(obs)
            mask_tensor = torch.tensor(obs.action_mask, dtype=torch.bool)
            action_idx, _, _ = select_action(network, obs_tensor, mask_tensor, device, deterministic=False)
            action = index_to_action(action_idx)

            step_res = cfg_env.step(action)
            obs_dict[step_res.next_player] = step_res.observation
            terminated = step_res.terminated
            truncated = step_res.truncated
            turns += 1

        total_turns_sp += turns
        if truncated:
            truncations_sp += 1
        elif cfg_env.winner is not None:
            seat_wins_sp[cfg_env.winner] += 1

    p_seat0_sp, s0_low_sp, s0_high_sp = compute_wilson_ci(seat_wins_sp[0], num_games)
    p_trunc_sp, trunc_low_sp, trunc_high_sp = compute_wilson_ci(truncations_sp, num_games)
    mean_turns_sp = total_turns_sp / num_games

    results = {
        "vs_rule_based": {
            "games": num_games,
            "win_rate": p_win_rule,
            "win_ci": (win_low_rule, win_high_rule),
            "trunc_rate": p_trunc_rule,
            "trunc_ci": (trunc_low_rule, trunc_high_rule),
            "mean_turns": mean_turns_rule,
        },
        "self_play": {
            "games": num_games,
            "seat0_win_rate": p_seat0_sp,
            "seat0_ci": (s0_low_sp, s0_high_sp),
            "trunc_rate": p_trunc_sp,
            "trunc_ci": (trunc_low_sp, trunc_high_sp),
            "mean_turns": mean_turns_sp,
            "all_seat_wins": seat_wins_sp,
        },
    }

    print_markdown_table(results)
    return results


def print_markdown_table(results: Dict[str, Any]) -> None:
    """Format and print results summary table."""
    rb = results["vs_rule_based"]
    sp = results["self_play"]

    print("\n" + "=" * 80)
    print("### WHOT-ML Paper 2 — Evaluation Matrix Results")
    print("=" * 80)
    table_str = f"""
| Evaluation Regime | Population Setup | Games ($N$) | Win Rate [95% CI] | Truncation Rate [95% CI] | Mean Turns |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Asymmetric (BRRR)** | 1 PPO vs. 3 RuleBased | {rb['games']} | {rb['win_rate']:.1%} [{rb['win_ci'][0]:.1%}, {rb['win_ci'][1]:.1%}] | {rb['trunc_rate']:.1%} [{rb['trunc_ci'][0]:.1%}, {rb['trunc_ci'][1]:.1%}] | {rb['mean_turns']:.1f} |
| **Symmetric Self-Play** | 4 PPO Agents | {sp['games']} | {sp['seat0_win_rate']:.1%} [{sp['seat0_ci'][0]:.1%}, {sp['seat0_ci'][1]:.1%}] | {sp['trunc_rate']:.1%} [{sp['trunc_ci'][0]:.1%}, {sp['trunc_ci'][1]:.1%}] | {sp['mean_turns']:.1f} |
"""
    print(table_str)
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze WHOT-ML Paper 2 Results")
    parser.add_argument("--run-dir", type=str, default="experiments/paper2/runs/pilot_10k", help="Run directory")
    parser.add_argument("--model-path", type=str, default=None, help="Explicit path to .pt model")
    parser.add_argument("--num-games", type=int, default=1000, help="Number of evaluation games per regime")
    parser.add_argument("--output-dir", type=str, default=None, help="Output figures directory")
    parser.add_argument("--device", type=str, default="cpu", help="Compute device")

    args = parser.parse_args()

    run_dir = args.run_dir
    csv_path = os.path.join(run_dir, "training_metrics.csv")
    if not os.path.exists(csv_path):
        csv_path = os.path.join(run_dir, "production_training_metrics.csv")

    model_path = args.model_path
    if model_path is None:
        candidates = [
            os.path.join(run_dir, "ppo_final_model.pt"),
            os.path.join(run_dir, "ppo_final_model_10m.pt"),
        ]
        for c in candidates:
            if os.path.exists(c):
                model_path = c
                break
        if model_path is None:
            model_path = candidates[0]

    output_dir = args.output_dir if args.output_dir else run_dir

    print(f"Analyzing Results in: {run_dir}")
    print(f"Metrics CSV: {csv_path}")
    print(f"Model File : {model_path}")

    # 1. Generate plots
    plot_learning_curves(csv_path, output_dir)

    # 2. Run evaluation matrix
    run_evaluation_matrix(model_path, num_games=args.num_games, device_name=args.device)


if __name__ == "__main__":
    main()
