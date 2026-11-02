"""Masked Actor-Critic Network for WHOT-ML Paper 2 (P2-D1 Section 3.A).

Implements separate Actor and Critic MLPs with Layer Normalization, ELU activations,
and large negative logit masking (-10^8) for discrete action spaces with illegal actions.
"""

from __future__ import annotations

from typing import Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F

MASK_NEG_INF: float = -1e8


class MaskedActorCritic(nn.Module):
    """Actor-Critic network with action masking for PPO in WHOT-ML.
    
    Actor Architecture:
      Linear(obs_dim, 256) -> LayerNorm(256) -> ELU() ->
      Linear(256, 256) -> LayerNorm(256) -> ELU() ->
      Linear(256, action_dim)
      
    Critic Architecture:
      Linear(obs_dim, 256) -> LayerNorm(256) -> ELU() ->
      Linear(256, 256) -> LayerNorm(256) -> ELU() ->
      Linear(256, 1)
    """

    def __init__(
        self,
        obs_dim: int = 280,
        action_dim: int = 76,
        hidden_dim: int = 256,
    ) -> None:
        super().__init__()
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim

        # Separate Actor trunk and head
        self.actor_trunk = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ELU(),
        )
        self.actor_head = nn.Linear(hidden_dim, action_dim)

        # Separate Critic trunk and head
        self.critic_trunk = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ELU(),
        )
        self.critic_head = nn.Linear(hidden_dim, 1)

    def compute_masked_logits(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Compute masked logits and boolean mask tensor.
        
        If mask is omitted, attempts to extract the last action_dim elements from x.
        """
        raw_logits = self.actor_head(self.actor_trunk(x))
        if mask is None:
            mask = x[..., -self.action_dim:]

        mask_bool = mask.bool()
        neg_val = torch.tensor(MASK_NEG_INF, dtype=raw_logits.dtype, device=raw_logits.device)
        masked_logits = torch.where(mask_bool, raw_logits, neg_val)
        return masked_logits, mask_bool

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass through Actor and Critic.
        
        Args:
            x: Observation tensor of shape (obs_dim,) or (batch_size, obs_dim).
            mask: Optional action mask of shape (action_dim,) or (batch_size, action_dim).
            
        Returns:
            action_probs: Probabilities of legal actions, shape (batch_size, action_dim)
                          or (action_dim,), with 0.0 for illegal actions.
            state_value: Critic value estimate, shape (batch_size, 1) or (1,).
        """
        is_unbatched = (x.dim() == 1)
        if is_unbatched:
            x = x.unsqueeze(0)
            if mask is not None and mask.dim() == 1:
                mask = mask.unsqueeze(0)

        # 1. Actor branch: masked logits & probabilities
        masked_logits, mask_bool = self.compute_masked_logits(x, mask)
        probs = F.softmax(masked_logits, dim=-1)

        # Strict zeroing for illegal actions to eliminate any floating-point residue
        probs = probs * mask_bool.to(probs.dtype)
        # Safe renormalization across valid legal action support
        probs_sum = probs.sum(dim=-1, keepdim=True).clamp(min=1e-12)
        probs = probs / probs_sum

        # 2. Critic branch: state value estimate V(s)
        value = self.critic_head(self.critic_trunk(x))

        if is_unbatched:
            probs = probs.squeeze(0)
            value = value.squeeze(0)

        return probs, value

    def get_value(self, x: torch.Tensor) -> torch.Tensor:
        """Evaluate the critic value V(s) alone."""
        return self.critic_head(self.critic_trunk(x))

    def get_masked_logits(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Retrieve the masked action logits (useful for Categorical distribution)."""
        masked_logits, _ = self.compute_masked_logits(x, mask)
        return masked_logits
