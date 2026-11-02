"""Main Training and Evaluation Script for Masked PPO in WHOT-ML Paper 2 (P2-D1).

Executes self-play PPO training with feedforward state encoding,
evaluates against baseline agents, logs metrics to CSV, and saves model checkpoints.
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import sys
from typing import Any, Dict, List, Optional, Tuple
import torch

# Ensure repository root is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from whot_ml.agents.rule_based_agent import RuleBasedAgent
from whot_ml.card import Shape
from whot_ml.environment import GameEnvironment
from whot_ml.observation import PlayerObservation
from whot_ml.ruleset import get_baseline_config

from experiments.paper2.envs.self_play_wrapper import SelfPlayEnvWrapper
from experiments.paper2.models.feedforward_encoder import FeedforwardEncoder
from experiments.paper2.models.ppo_network import MaskedActorCritic
from experiments.paper2.training.ppo_trainer import PPOTrainer
from experiments.paper2.training.rollout_buffer import RolloutBuffer


def select_action(
    network: MaskedActorCritic,
    obs_tensor: torch.Tensor,
    mask: torch.Tensor,
    device: torch.device,
    deterministic: bool = False,
) -> Tuple[int, float, float]:
    """Sample an action from the policy network given an encoded observation."""
    with torch.no_grad():
        x = obs_tensor.unsqueeze(0).to(device)
        m = mask.unsqueeze(0).to(device)

        masked_logits, _ = network.compute_masked_logits(x, m)
        dist = torch.distributions.Categorical(logits=masked_logits)

        if deterministic:
            # Pick argmax among legal actions
            action = torch.argmax(masked_logits, dim=-1).item()
            log_prob = dist.log_prob(torch.tensor([action], device=device)).item()
        else:
            action_tensor = dist.sample()
            action = action_tensor.item()
            log_prob = dist.log_prob(action_tensor).item()

        value = network.get_value(x).item()

    return action, log_prob, value


def evaluate_policy(
    network: MaskedActorCritic,
    encoder: FeedforwardEncoder,
    num_episodes: int = 50,
    eval_mode: str = "vs_rule_based",
    base_seed: int = 60000,
    device: torch.device = torch.device("cpu"),
) -> Dict[str, float]:
    """Evaluate frozen policy in self-play or against RuleBasedAgent opponents."""
    network.eval()
    rl_wins = 0
    truncations = 0
    total_turns = 0

    rule_agents = [RuleBasedAgent(name=f"RuleBased_{i}") for i in range(4)]

    for ep in range(num_episodes):
        seed = base_seed + ep
        cfg = get_baseline_config()
        cfg_env = GameEnvironment(config=cfg)
        obs_dict = cfg_env.reset(seed=seed)

        terminated = False
        truncated = False
        turns = 0

        while not (terminated or truncated):
            curr_p = cfg_env.current_player
            obs = obs_dict[curr_p]

            if eval_mode == "vs_rule_based":
                # Seat 0 is RL agent, Seats 1..3 are RuleBasedAgent
                if curr_p == 0:
                    obs_tensor = encoder.encode(obs)
                    mask_tensor = torch.tensor(obs.action_mask, dtype=torch.bool)
                    action_idx, _, _ = select_action(
                        network, obs_tensor, mask_tensor, device, deterministic=True
                    )
                    from whot_ml.action import index_to_action
                    action = index_to_action(action_idx)
                else:
                    action = rule_agents[curr_p].act(obs)
            else:
                # Pure self-play evaluation
                obs_tensor = encoder.encode(obs)
                mask_tensor = torch.tensor(obs.action_mask, dtype=torch.bool)
                action_idx, _, _ = select_action(
                    network, obs_tensor, mask_tensor, device, deterministic=True
                )
                from whot_ml.action import index_to_action
                action = index_to_action(action_idx)

            step_res = cfg_env.step(action)
            obs_dict[step_res.next_player] = step_res.observation
            terminated = step_res.terminated
            truncated = step_res.truncated
            turns += 1

        total_turns += turns
        if truncated:
            truncations += 1
        elif cfg_env.winner == 0:
            rl_wins += 1

    network.train()
    win_rate = float(rl_wins) / float(num_episodes)
    trunc_rate = float(truncations) / float(num_episodes)
    mean_turns = float(total_turns) / float(num_episodes)

    return {
        "win_rate": win_rate,
        "truncation_rate": trunc_rate,
        "mean_turns": mean_turns,
    }


def train_ppo(
    total_timesteps: int = 10000,
    buffer_size: int = 2048,
    mini_batch_size: int = 64,
    lr: float = 3e-4,
    eval_interval: int = 2500,
    eval_episodes: int = 20,
    save_interval: int = 5000,
    run_dir: str = "experiments/paper2/runs/test_run",
    seed: int = 42,
    device_name: str = "cpu",
) -> Tuple[MaskedActorCritic, Dict[str, Any]]:
    """Execute PPO training loop with periodic evaluation and checkpointing."""
    random.seed(seed)
    torch.manual_seed(seed)
    device = torch.device(device_name)

    os.makedirs(run_dir, exist_ok=True)
    csv_path = os.path.join(run_dir, "training_metrics.csv")

    env = SelfPlayEnvWrapper(num_players=4)
    encoder = FeedforwardEncoder(num_players=4)
    network = MaskedActorCritic(obs_dim=280, action_dim=76, hidden_dim=256).to(device)
    buffer = RolloutBuffer(buffer_size=buffer_size, obs_dim=280, action_dim=76, num_players=4, device=device)
    trainer = PPOTrainer(network=network, lr=lr, mini_batch_size=mini_batch_size)

    # Initialize CSV logger
    csv_headers = [
        "step",
        "actor_loss",
        "critic_loss",
        "entropy",
        "total_loss",
        "eval_win_rate",
        "eval_trunc_rate",
        "eval_mean_turns",
    ]
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)

    obs = env.reset(seed=seed)
    current_step = 0
    episodes_completed = 0
    latest_eval: Dict[str, float] = {"win_rate": 0.0, "truncation_rate": 0.0, "mean_turns": 0.0}

    print(f"Starting PPO Training: {total_timesteps} steps, buffer size {buffer_size}")

    while current_step < total_timesteps:
        # Encode observation
        obs_tensor = encoder.encode(obs)
        mask_tensor = torch.tensor(obs.action_mask, dtype=torch.bool)
        acting_player = env.current_player

        # Select action
        action_idx, log_prob, value = select_action(
            network, obs_tensor, mask_tensor, device, deterministic=False
        )

        # Step environment
        next_obs, reward, done, info = env.step(action_idx)
        current_step += 1

        # Store transition in buffer
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

        # Check if buffer is ready for update
        if buffer.full or (current_step >= total_timesteps and buffer.step_idx > 0):
            # Compute bootstrap value for the next observation if episode not finished
            last_val = 0.0
            if not done:
                next_tensor = encoder.encode(obs).unsqueeze(0).to(device)
                with torch.no_grad():
                    last_val = network.get_value(next_tensor).item()

            buffer.compute_gae_and_returns(last_values=last_val, per_player=True)
            losses = trainer.update(buffer)
            buffer.reset()

            print(
                f"[Step {current_step}/{total_timesteps}] "
                f"Loss: {losses['total_loss']:.4f} "
                f"(Actor: {losses['actor_loss']:.4f}, Critic: {losses['critic_loss']:.4f}, Ent: {losses['entropy']:.4f})"
            )

            # Periodic Evaluation
            if current_step % eval_interval < buffer_size or current_step >= total_timesteps:
                latest_eval = evaluate_policy(
                    network, encoder, num_episodes=eval_episodes, device=device
                )
                print(
                    f"  -> Eval vs RuleBased: Win Rate = {latest_eval['win_rate']:.2%}, "
                    f"Truncation = {latest_eval['truncation_rate']:.2%}, "
                    f"Mean Turns = {latest_eval['mean_turns']:.1f}"
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
                ])

        # Periodic Checkpointing
        if current_step % save_interval < 1 or current_step >= total_timesteps:
            ckpt_path = os.path.join(run_dir, f"ppo_checkpoint_step_{current_step}.pt")
            torch.save(network.state_dict(), ckpt_path)

    final_model_path = os.path.join(run_dir, "ppo_final_model.pt")
    torch.save(network.state_dict(), final_model_path)
    print(f"Training finished. Final weights saved to {final_model_path}")

    return network, latest_eval


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Masked PPO in WHOT-ML")
    parser.add_argument("--total-timesteps", type=int, default=10000, help="Total environment timesteps")
    parser.add_argument("--buffer-size", type=int, default=2048, help="Rollout buffer capacity")
    parser.add_argument("--batch-size", type=int, default=64, help="PPO mini-batch size")
    parser.add_argument("--lr", type=float, default=3e-4, help="Actor learning rate")
    parser.add_argument("--eval-interval", type=int, default=2500, help="Evaluation frequency in steps")
    parser.add_argument("--eval-episodes", type=int, default=20, help="Number of evaluation games")
    parser.add_argument("--save-interval", type=int, default=5000, help="Checkpoint frequency in steps")
    parser.add_argument("--run-dir", type=str, default="experiments/paper2/runs/test_run", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--device", type=str, default="cpu", help="Compute device (cpu, cuda)")

    args = parser.parse_args()

    train_ppo(
        total_timesteps=args.total_timesteps,
        buffer_size=args.buffer_size,
        mini_batch_size=args.batch_size,
        lr=args.lr,
        eval_interval=args.eval_interval,
        eval_episodes=args.eval_episodes,
        save_interval=args.save_interval,
        run_dir=args.run_dir,
        seed=args.seed,
        device_name=args.device,
    )


if __name__ == "__main__":
    main()
