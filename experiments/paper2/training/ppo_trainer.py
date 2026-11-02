"""PPO Trainer with Action Masking for WHOT-ML Paper 2 (P2-D1).

Implements Proximal Policy Optimization with advantage normalization,
clipped surrogate objective, critic value loss, and entropy bonus over legal actions.
"""

from __future__ import annotations

from typing import Dict, Optional, Union
import torch
import torch.nn as nn
import torch.nn.functional as F

from experiments.paper2.models.ppo_network import MaskedActorCritic
from experiments.paper2.training.rollout_buffer import RolloutBuffer


class PPOTrainer:
    """PPO Trainer supporting discrete masked action spaces.
    
    Hyperparameters (matching P2-D1 Table 3.A):
      - lr: 3e-4 (Actor)
      - critic_lr: 1e-3 (Critic)
      - clip_eps: 0.20
      - ent_coef: 0.01
      - vf_coef: 0.50
      - max_grad_norm: 0.50
      - ppo_epochs: 4
      - mini_batch_size: 64 (or 512 for production)
    """

    def __init__(
        self,
        network: MaskedActorCritic,
        optimizer: Optional[torch.optim.Optimizer] = None,
        lr: float = 3e-4,
        critic_lr: float = 1e-3,
        clip_eps: float = 0.20,
        ent_coef: float = 0.01,
        vf_coef: float = 0.50,
        max_grad_norm: float = 0.50,
        ppo_epochs: int = 4,
        mini_batch_size: int = 64,
    ) -> None:
        self.network = network
        self.clip_eps = clip_eps
        self.ent_coef = ent_coef
        self.vf_coef = vf_coef
        self.max_grad_norm = max_grad_norm
        self.ppo_epochs = ppo_epochs
        self.mini_batch_size = mini_batch_size

        if optimizer is not None:
            self.optimizer = optimizer
        else:
            self.optimizer = torch.optim.Adam(
                [
                    {"params": network.actor_trunk.parameters(), "lr": lr},
                    {"params": network.actor_head.parameters(), "lr": lr},
                    {"params": network.critic_trunk.parameters(), "lr": critic_lr},
                    {"params": network.critic_head.parameters(), "lr": critic_lr},
                ],
                eps=1e-7,
            )

    def update(self, buffer: RolloutBuffer) -> Dict[str, float]:
        """Perform PPO mini-batch updates on transitions stored in the buffer.
        
        Args:
            buffer: RolloutBuffer with computed advantages and returns.
            
        Returns:
            Dictionary with mean losses: actor_loss, critic_loss, entropy, total_loss.
        """
        valid_steps = buffer.step_idx
        if valid_steps == 0:
            return {
                "actor_loss": 0.0,
                "critic_loss": 0.0,
                "entropy": 0.0,
                "total_loss": 0.0,
            }

        # 1. Normalize advantages across all valid transitions (mean 0, std 1)
        valid_adv = buffer.advantages[:valid_steps]
        adv_mean = valid_adv.mean()
        adv_std = valid_adv.std()
        normalized_adv = (valid_adv - adv_mean) / (adv_std + 1e-8)
        buffer.advantages[:valid_steps] = normalized_adv

        epoch_actor_losses = []
        epoch_critic_losses = []
        epoch_entropies = []
        epoch_total_losses = []

        # 2. Optimization epochs
        for _ in range(self.ppo_epochs):
            for batch in buffer.get_batches(self.mini_batch_size):
                obs = batch["observations"]
                actions = batch["actions"]
                old_log_probs = batch["log_probs"]
                advantages = batch["advantages"]
                returns = batch["returns"]
                masks = batch["masks"]

                # Forward pass through policy network
                masked_logits, _ = self.network.compute_masked_logits(obs, masks)
                dist = torch.distributions.Categorical(logits=masked_logits)
                new_log_probs = dist.log_prob(actions)
                entropy = dist.entropy().mean()

                # Forward pass through critic network
                values = self.network.get_value(obs).squeeze(-1)

                # Clipped surrogate objective
                ratio = torch.exp(new_log_probs - old_log_probs)
                surr1 = ratio * advantages
                surr2 = torch.clamp(ratio, 1.0 - self.clip_eps, 1.0 + self.clip_eps) * advantages
                actor_loss = -torch.min(surr1, surr2).mean()

                # Critic loss (MSE)
                critic_loss = F.mse_loss(values, returns)

                # Total combined loss
                total_loss = actor_loss + self.vf_coef * critic_loss - self.ent_coef * entropy

                # Backward and optimization step
                self.optimizer.zero_grad()
                total_loss.backward()
                nn.utils.clip_grad_norm_(self.network.parameters(), self.max_grad_norm)
                self.optimizer.step()

                epoch_actor_losses.append(actor_loss.item())
                epoch_critic_losses.append(critic_loss.item())
                epoch_entropies.append(entropy.item())
                epoch_total_losses.append(total_loss.item())

        mean_actor = float(sum(epoch_actor_losses) / len(epoch_actor_losses)) if epoch_actor_losses else 0.0
        mean_critic = float(sum(epoch_critic_losses) / len(epoch_critic_losses)) if epoch_critic_losses else 0.0
        mean_entropy = float(sum(epoch_entropies) / len(epoch_entropies)) if epoch_entropies else 0.0
        mean_total = float(sum(epoch_total_losses) / len(epoch_total_losses)) if epoch_total_losses else 0.0

        return {
            "actor_loss": mean_actor,
            "critic_loss": mean_critic,
            "entropy": mean_entropy,
            "total_loss": mean_total,
        }
