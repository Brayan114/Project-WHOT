"""Production PPO Training Script for Kaggle (10M Timesteps) - WHOT-ML Paper 2.

Designed for high-throughput GPU training on Kaggle (P100 / T4 / A100).
Configures large rollout buffers (8,192), batch size (256/512), periodic evaluation
against RuleBasedAgent baselines, and artifact persistence in /kaggle/working/.
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import sys
import time
from typing import Any, Dict, Optional, Tuple
import torch

# Ensure repository root is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiments.paper2.envs.self_play_wrapper import SelfPlayEnvWrapper
from experiments.paper2.models.feedforward_encoder import FeedforwardEncoder
from experiments.paper2.models.ppo_network import MaskedActorCritic
from experiments.paper2.scripts.train_ppo import evaluate_policy, select_action
from experiments.paper2.training.ppo_trainer import PPOTrainer
from experiments.paper2.training.rollout_buffer import RolloutBuffer


def get_default_output_dir() -> str:
    """Detect whether running inside a Kaggle notebook environment."""
    if os.path.exists("/kaggle/working"):
        return "/kaggle/working/whot_ppo_10m"
    return os.path.join(REPO_ROOT, "experiments/paper2/runs/kaggle_10m_local")


def run_kaggle_training(
    total_timesteps: int = 10_000_000,
    buffer_size: int = 8192,
    mini_batch_size: int = 256,
    lr: float = 3e-4,
    critic_lr: float = 1e-3,
    eval_interval: int = 100_000,
    eval_episodes: int = 50,
    save_interval: int = 250_000,
    run_dir: Optional[str] = None,
    seed: int = 42,
) -> None:
    if run_dir is None:
        run_dir = get_default_output_dir()

    os.makedirs(run_dir, exist_ok=True)
    csv_path = os.path.join(run_dir, "production_training_metrics.csv")

    # Detect compute device
    if torch.cuda.is_available():
        device = torch.device("cuda")
        gpu_name = torch.cuda.get_device_name(0)
        print(f"CUDA accelerator detected: {gpu_name}")
    else:
        device = torch.device("cpu")
        print("No CUDA device detected. Running on CPU.")

    print("================================================================")
    print("WHOT-ML Paper 2 — Production PPO Self-Play Training (Kaggle)")
    print(f"Target Budget : {total_timesteps:,} environment timesteps")
    print(f"Rollout Buffer: {buffer_size:,} transitions per update")
    print(f"Mini-batch    : {mini_batch_size} samples")
    print(f"Learning Rate : Actor {lr:.2e}, Critic {critic_lr:.2e}")
    print(f"Eval Interval : Every {eval_interval:,} steps ({eval_episodes} games)")
    print(f"Checkpointing : Every {save_interval:,} steps")
    print(f"Output Path   : {run_dir}")
    print(f"Random Seed   : {seed}")
    print("================================================================")

    # Determinism
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    # Initialize environment, model, and buffer
    env = SelfPlayEnvWrapper(num_players=4)
    encoder = FeedforwardEncoder(num_players=4)
    network = MaskedActorCritic(obs_dim=280, action_dim=76, hidden_dim=256).to(device)
    buffer = RolloutBuffer(
        buffer_size=buffer_size,
        obs_dim=280,
        action_dim=76,
        num_players=4,
        device=device,
    )
    trainer = PPOTrainer(
        network=network,
        lr=lr,
        critic_lr=critic_lr,
        clip_eps=0.20,
        ent_coef=0.01,
        vf_coef=0.50,
        max_grad_norm=0.50,
        ppo_epochs=4,
        mini_batch_size=mini_batch_size,
    )

    # CSV Metric Logging
    csv_headers = [
        "step",
        "actor_loss",
        "critic_loss",
        "entropy",
        "total_loss",
        "eval_win_rate",
        "eval_trunc_rate",
        "eval_mean_turns",
        "elapsed_sec",
    ]
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)

    obs = env.reset(seed=seed)
    current_step = 0
    episodes_completed = 0
    start_time = time.time()
    last_eval_step = 0
    latest_eval = {"win_rate": 0.0, "truncation_rate": 0.0, "mean_turns": 0.0}

    while current_step < total_timesteps:
        obs_tensor = encoder.encode(obs)
        mask_tensor = torch.tensor(obs.action_mask, dtype=torch.bool)
        acting_player = env.current_player

        action_idx, log_prob, value = select_action(
            network, obs_tensor, mask_tensor, device, deterministic=False
        )

        next_obs, reward, done, info = env.step(action_idx)
        current_step += 1

        buffer.add(
            obs=obs_tensor,
            action=action_idx,
            log_prob=log_prob,
            reward=reward,
            value=value,
            mask=mask_tensor,
            done=done,
            player_id=acting_player,
        )

        if done:
            episodes_completed += 1
            buffer.finalize_episode(info["player_rewards"])
            obs = env.reset(seed=seed + episodes_completed)
        else:
            obs = next_obs

        # Update upon filling buffer or hitting final timestep
        if buffer.full or (current_step >= total_timesteps and buffer.step_idx > 0):
            last_val = 0.0
            if not done:
                next_tensor = encoder.encode(obs).unsqueeze(0).to(device)
                with torch.no_grad():
                    last_val = network.get_value(next_tensor).item()

            buffer.compute_gae_and_returns(last_values=last_val, per_player=True)
            losses = trainer.update(buffer)
            buffer.reset()

            elapsed = time.time() - start_time
            fps = current_step / max(elapsed, 1e-4)

            print(
                f"[Step {current_step:8d}/{total_timesteps:,}] "
                f"FPS: {fps:6.1f} | "
                f"Loss: {losses['total_loss']:+.4f} "
                f"(Actor: {losses['actor_loss']:+.4f}, Critic: {losses['critic_loss']:.4f}, Ent: {losses['entropy']:.4f})"
            )

            # Periodic Evaluation
            if current_step - last_eval_step >= eval_interval or current_step >= total_timesteps:
                last_eval_step = current_step
                print(f"--- Running Evaluation ({eval_episodes} games vs RuleBasedAgent) ---")
                latest_eval = evaluate_policy(
                    network,
                    encoder,
                    num_episodes=eval_episodes,
                    eval_mode="vs_rule_based",
                    base_seed=70000 + (current_step // 1000),
                    device=device,
                )
                print(
                    f"  -> Evaluation Result @ Step {current_step:,}: "
                    f"Win Rate: {latest_eval['win_rate']:.2%}, "
                    f"Truncation: {latest_eval['truncation_rate']:.2%}, "
                    f"Mean Turns: {latest_eval['mean_turns']:.1f}"
                )

            # Log to CSV
            with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    current_step,
                    losses["actor_loss"],
                    losses["critic_loss"],
                    losses["entropy"],
                    losses["total_loss"],
                    latest_eval["win_rate"],
                    latest_eval["truncation_rate"],
                    latest_eval["mean_turns"],
                    round(elapsed, 2),
                ])

        # Periodic Checkpointing
        if current_step % save_interval < buffer_size or current_step >= total_timesteps:
            ckpt_path = os.path.join(run_dir, f"ppo_checkpoint_{current_step // 1000}k.pt")
            torch.save(network.state_dict(), ckpt_path)

    final_model_path = os.path.join(run_dir, "ppo_final_model_10m.pt")
    torch.save(network.state_dict(), final_model_path)
    total_time = time.time() - start_time
    print("================================================================")
    print(f"Production Training Complete in {total_time / 3600:.2f} hours.")
    print(f"Final Weights Saved: {final_model_path}")
    print(f"Metrics CSV Saved  : {csv_path}")
    print("================================================================")


def main() -> None:
    parser = argparse.ArgumentParser(description="Kaggle PPO Production Training for WHOT-ML")
    parser.add_argument("--total-timesteps", type=int, default=10_000_000)
    parser.add_argument("--buffer-size", type=int, default=8192)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--critic-lr", type=float, default=1e-3)
    parser.add_argument("--eval-interval", type=int, default=100_000)
    parser.add_argument("--eval-episodes", type=int, default=50)
    parser.add_argument("--save-interval", type=int, default=250_000)
    parser.add_argument("--run-dir", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()

    run_kaggle_training(
        total_timesteps=args.total_timesteps,
        buffer_size=args.buffer_size,
        mini_batch_size=args.batch_size,
        lr=args.lr,
        critic_lr=args.critic_lr,
        eval_interval=args.eval_interval,
        eval_episodes=args.eval_episodes,
        save_interval=args.save_interval,
        run_dir=args.run_dir,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
