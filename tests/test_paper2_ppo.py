"""Unit tests for PPO Trainer and main training loop (P2-D1)."""

import math
import os
import pytest
import torch

from experiments.paper2.models.ppo_network import MaskedActorCritic
from experiments.paper2.training.ppo_trainer import PPOTrainer
from experiments.paper2.training.rollout_buffer import RolloutBuffer
from experiments.paper2.scripts.train_ppo import train_ppo


def test_ppo_trainer_update_changes_weights_and_losses_finite():
    """Verify that PPOTrainer.update() computes finite losses and updates parameters."""
    torch.manual_seed(42)
    network = MaskedActorCritic(obs_dim=280, action_dim=76, hidden_dim=256)
    initial_actor_weight = network.actor_head.weight.clone()
    initial_critic_weight = network.critic_head.weight.clone()

    buffer_size = 16
    buffer = RolloutBuffer(buffer_size=buffer_size, obs_dim=280, action_dim=76, num_players=4)

    # Populate buffer with dummy transitions
    for i in range(buffer_size):
        obs = torch.randn(280)
        action = i % 10
        log_prob = -1.5
        reward = 1.0 if i == (buffer_size - 1) else 0.0
        value = 0.1 * i
        mask = torch.zeros(76, dtype=torch.bool)
        mask[0:10] = True  # first 10 actions are legal
        done = (i == (buffer_size - 1))
        player_id = i % 4

        buffer.add(
            obs=obs,
            action=action,
            log_prob=log_prob,
            reward=reward,
            value=value,
            mask=mask,
            done=done,
            player_id=player_id,
        )

    buffer.compute_gae_and_returns(last_values=0.0, per_player=True)

    trainer = PPOTrainer(
        network=network,
        lr=1e-3,
        critic_lr=1e-3,
        clip_eps=0.20,
        ent_coef=0.01,
        vf_coef=0.50,
        max_grad_norm=0.50,
        ppo_epochs=2,
        mini_batch_size=8,
    )

    losses = trainer.update(buffer)

    # 1. Assert all losses are finite
    assert math.isfinite(losses["actor_loss"])
    assert math.isfinite(losses["critic_loss"])
    assert math.isfinite(losses["entropy"])
    assert math.isfinite(losses["total_loss"])

    # 2. Assert network parameters updated
    assert not torch.equal(network.actor_head.weight, initial_actor_weight)
    assert not torch.equal(network.critic_head.weight, initial_critic_weight)


def test_train_ppo_tiny_run(tmp_path):
    """Verify that train_ppo() executes without error, logs CSV, and produces checkpoints."""
    run_dir = str(tmp_path / "tiny_run")

    network, latest_eval = train_ppo(
        total_timesteps=60,
        buffer_size=20,
        mini_batch_size=10,
        lr=3e-4,
        eval_interval=30,
        eval_episodes=2,
        save_interval=30,
        run_dir=run_dir,
        seed=101,
    )

    # 1. Verify model and evaluation results
    assert isinstance(network, MaskedActorCritic)
    assert "win_rate" in latest_eval
    assert "truncation_rate" in latest_eval

    # 2. Verify files created on disk
    csv_file = os.path.join(run_dir, "training_metrics.csv")
    final_model = os.path.join(run_dir, "ppo_final_model.pt")

    assert os.path.exists(csv_file), f"CSV metrics log missing at {csv_file}"
    assert os.path.exists(final_model), f"Final model checkpoint missing at {final_model}"

    # 3. Verify CSV contents
    with open(csv_file, mode="r", encoding="utf-8") as f:
        lines = f.readlines()
        # Expect header + at least 2 update rows
        assert len(lines) >= 3
