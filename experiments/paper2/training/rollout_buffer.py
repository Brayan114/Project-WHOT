"""Multi-Agent Rollout Buffer with GAE computation for WHOT-ML Paper 2 (P2-D1).

Stores transitions for turn-based multi-agent self-play and computes Generalized
Advantage Estimation (GAE) and returns while correctly distributing terminal rewards
across all participating players.
"""

from __future__ import annotations

from typing import Dict, Generator, List, Optional, Tuple, Union
import torch


class RolloutBuffer:
    """Trajectory storage and GAE computation for multi-agent self-play PPO.
    
    Fields stored per step:
      - observations: (buffer_size, obs_dim) float32
      - actions: (buffer_size,) int64
      - log_probs: (buffer_size,) float32
      - rewards: (buffer_size,) float32
      - values: (buffer_size,) float32
      - masks: (buffer_size, action_dim) bool
      - dones: (buffer_size,) bool
      - player_ids: (buffer_size,) int64
      - advantages: (buffer_size,) float32
      - returns: (buffer_size,) float32
    """

    def __init__(
        self,
        buffer_size: int,
        obs_dim: int = 280,
        action_dim: int = 76,
        num_players: int = 4,
        device: Union[str, torch.device] = "cpu",
    ) -> None:
        self.buffer_size: int = buffer_size
        self.obs_dim: int = obs_dim
        self.action_dim: int = action_dim
        self.num_players: int = num_players
        self.device = torch.device(device)

        # Allocate storage tensors
        self.observations = torch.zeros((buffer_size, obs_dim), dtype=torch.float32, device=self.device)
        self.actions = torch.zeros((buffer_size,), dtype=torch.long, device=self.device)
        self.log_probs = torch.zeros((buffer_size,), dtype=torch.float32, device=self.device)
        self.rewards = torch.zeros((buffer_size,), dtype=torch.float32, device=self.device)
        self.values = torch.zeros((buffer_size,), dtype=torch.float32, device=self.device)
        self.masks = torch.zeros((buffer_size, action_dim), dtype=torch.bool, device=self.device)
        self.dones = torch.zeros((buffer_size,), dtype=torch.bool, device=self.device)
        self.player_ids = torch.zeros((buffer_size,), dtype=torch.long, device=self.device)

        # Computed targets
        self.advantages = torch.zeros((buffer_size,), dtype=torch.float32, device=self.device)
        self.returns = torch.zeros((buffer_size,), dtype=torch.float32, device=self.device)

        self.step_idx: int = 0
        self.full: bool = False

    def reset(self) -> None:
        """Clear the buffer for the next training iteration."""
        self.step_idx = 0
        self.full = False

    def add(
        self,
        obs: Union[torch.Tensor, List[float]],
        action: int,
        log_prob: float,
        reward: float,
        value: float,
        mask: Union[torch.Tensor, List[int], List[bool]],
        done: bool,
        player_id: int = 0,
    ) -> int:
        """Append a single step transition to the buffer.
        
        Args:
            obs: Observation vector (280-dim).
            action: Selected discrete action index (0..75).
            log_prob: Log probability of the selected action.
            reward: Step reward.
            value: Critic value estimate V(s).
            mask: Boolean action mask (76-dim).
            done: Termination flag.
            player_id: Seat index of the acting player.
            
        Returns:
            Current step index in buffer.
        """
        if self.step_idx >= self.buffer_size:
            raise IndexError(f"RolloutBuffer overflow: capacity {self.buffer_size} reached")

        idx = self.step_idx

        # Assign tensors
        if not isinstance(obs, torch.Tensor):
            obs = torch.tensor(obs, dtype=torch.float32, device=self.device)
        self.observations[idx] = obs.to(device=self.device)

        self.actions[idx] = int(action)
        self.log_probs[idx] = float(log_prob)
        self.rewards[idx] = float(reward)
        self.values[idx] = float(value)

        if not isinstance(mask, torch.Tensor):
            mask = torch.tensor(mask, dtype=torch.bool, device=self.device)
        self.masks[idx] = mask.bool().to(device=self.device)

        self.dones[idx] = bool(done)
        self.player_ids[idx] = int(player_id)

        self.step_idx += 1
        if self.step_idx >= self.buffer_size:
            self.full = True

        return idx

    def finalize_episode(self, player_rewards: Dict[int, float]) -> None:
        """Assign terminal rewards to the final transitions of each player in the episode.
        
        In turn-based multi-agent play:
          - Step T terminates the game (winner gets +1.0).
          - Other participating players took their last actions at prior steps.
          - This method searches backward from the current buffer pointer to update
            each player's most recent transition with their terminal payoff and sets done=True.
        """
        if self.step_idx == 0:
            return

        players_to_update = set(player_rewards.keys())
        # Walk backward from the last inserted transition
        for idx in range(self.step_idx - 1, -1, -1):
            p = int(self.player_ids[idx].item())
            if p in players_to_update:
                self.rewards[idx] = float(player_rewards[p])
                self.dones[idx] = True
                players_to_update.remove(p)
                if not players_to_update:
                    break

    def compute_gae_and_returns(
        self,
        last_values: Union[float, Dict[int, float], torch.Tensor, Sequence[float]],
        gamma: float = 0.995,
        tau: float = 0.95,
        per_player: bool = True,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Compute Generalized Advantage Estimation (GAE) and target returns.
        
        Args:
            last_values: Critic bootstrap value V(s_last) for incomplete episodes.
                         Can be a dict mapping player_id -> float, a tensor of length num_players,
                         or a scalar float.
            gamma: Discount factor (default: 0.995 per P2-D1).
            tau: GAE smoothing parameter lambda (default: 0.95 per P2-D1).
            per_player: If True, computes GAE along each player's individual turn sequence.
                        If False, computes GAE along the sequential buffer.
                        
        Returns:
            advantages: (buffer_size,) float32 tensor
            returns: (buffer_size,) float32 tensor
        """
        valid_steps = self.step_idx
        if valid_steps == 0:
            return self.advantages, self.returns

        # Normalize last_values lookup
        last_vals: Dict[int, float] = {}
        if isinstance(last_values, dict):
            last_vals = {int(k): float(v) for k, v in last_values.items()}
        elif isinstance(last_values, (list, tuple)):
            last_vals = {p: float(last_values[p]) for p in range(len(last_values))}
        elif isinstance(last_values, torch.Tensor):
            if last_values.numel() == 1:
                last_vals = {p: float(last_values.item()) for p in range(self.num_players)}
            else:
                last_vals = {p: float(last_values[p].item()) for p in range(last_values.numel())}
        else:
            last_vals = {p: float(last_values) for p in range(self.num_players)}

        if per_player:
            # Multi-agent turn-based GAE: compute GAE along each player's decision path
            for p in range(self.num_players):
                player_indices = [
                    t for t in range(valid_steps) if int(self.player_ids[t].item()) == p
                ]
                if not player_indices:
                    continue

                last_gae = 0.0
                next_val = last_vals.get(p, 0.0)

                for idx in reversed(player_indices):
                    r_t = self.rewards[idx].item()
                    v_t = self.values[idx].item()
                    d_t = 1.0 if self.dones[idx].item() else 0.0

                    non_terminal = 1.0 - d_t
                    delta = r_t + gamma * next_val * non_terminal - v_t
                    last_gae = delta + gamma * tau * non_terminal * last_gae

                    self.advantages[idx] = last_gae
                    self.returns[idx] = last_gae + v_t

                    next_val = v_t
        else:
            # Sequential GAE across contiguous steps
            last_gae = 0.0
            next_val = last_vals.get(0, 0.0)

            for idx in range(valid_steps - 1, -1, -1):
                r_t = self.rewards[idx].item()
                v_t = self.values[idx].item()
                d_t = 1.0 if self.dones[idx].item() else 0.0

                non_terminal = 1.0 - d_t
                delta = r_t + gamma * next_val * non_terminal - v_t
                last_gae = delta + gamma * tau * non_terminal * last_gae

                self.advantages[idx] = last_gae
                self.returns[idx] = last_gae + v_t

                next_val = v_t

        return self.advantages, self.returns

    def get_batches(
        self,
        batch_size: int,
    ) -> Generator[Dict[str, torch.Tensor], None, None]:
        """Generate randomized mini-batches for PPO policy and value updates."""
        valid_steps = self.step_idx
        if valid_steps == 0:
            return

        indices = torch.randperm(valid_steps, device=self.device)

        for start_idx in range(0, valid_steps, batch_size):
            batch_indices = indices[start_idx : start_idx + batch_size]
            yield {
                "observations": self.observations[batch_indices],
                "actions": self.actions[batch_indices],
                "log_probs": self.log_probs[batch_indices],
                "advantages": self.advantages[batch_indices],
                "returns": self.returns[batch_indices],
                "masks": self.masks[batch_indices],
                "values": self.values[batch_indices],
            }
