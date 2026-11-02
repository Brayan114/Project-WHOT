"""Multi-Agent Self-Play Environment Wrapper for WHOT-ML Paper 2 (P2-D1).

Wraps a single GameEnvironment to manage a 4-player turn-based self-play game
with sparse terminal rewards (+1.0 for winner, -1.0 for losers).
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, List, Optional, Tuple, Union
import torch

from whot_ml.action import Action, index_to_action
from whot_ml.environment import GameEnvironment
from whot_ml.observation import PlayerObservation
from whot_ml.ruleset import WHOTConfig, get_baseline_config


class SelfPlayEnvWrapper:
    """Self-play environment wrapper for 4-player WHOT.
    
    API:
      reset(seed: Optional[int]) -> PlayerObservation
      step(action: Union[int, Action]) -> Tuple[PlayerObservation, float, bool, Dict[str, Any]]
      action_mask(player_id: Optional[int]) -> List[int]
    """

    def __init__(
        self,
        env: Optional[GameEnvironment] = None,
        config: Optional[WHOTConfig] = None,
        num_players: int = 4,
    ) -> None:
        if env is not None:
            self.env = env
        else:
            cfg = config if config is not None else get_baseline_config()
            if cfg.player_count != num_players:
                cfg = replace(cfg, player_count=num_players)
            self.env = GameEnvironment(config=cfg)

        self.num_players: int = self.env.config.player_count
        self._last_obs: Optional[PlayerObservation] = None

    @property
    def current_player(self) -> int:
        """The player index whose turn it is to act."""
        return self.env.current_player

    @property
    def is_terminal(self) -> bool:
        """True if the game has terminated (victory or truncation)."""
        return self.env.is_terminal

    @property
    def winner(self) -> Optional[int]:
        """Winning player index, or None if unfinished or truncated."""
        return self.env.winner

    def action_mask(self, player_id: Optional[int] = None) -> List[int]:
        """76-slot action mask for the specified player (default: current_player)."""
        return self.env.action_mask(player_id)

    def reset(self, seed: Optional[int] = None) -> PlayerObservation:
        """Reset the game and return the observation for the initial acting player."""
        obs_dict = self.env.reset(seed=seed)
        acting_player = self.env.current_player
        self._last_obs = obs_dict[acting_player]
        return self._last_obs

    def step(
        self,
        action: Union[int, Action],
    ) -> Tuple[PlayerObservation, float, bool, Dict[str, Any]]:
        """Execute a move for the current player.
        
        Args:
            action: Discrete action index (0..75) or Action object.
            
        Returns:
            obs: PlayerObservation for the next acting player (or acting player on termination).
            reward: float. 0.0 for intermediate moves; on termination, +1.0 for winner, -1.0 for loser.
            done: bool. True if terminated (shedding) or truncated.
            info: Metadata dict containing acting_player, next_player, winner, player_rewards, action_mask.
        """
        if self.env.state is None:
            raise RuntimeError("Environment not initialized; call reset() first")

        acting_player = self.env.current_player

        # Convert discrete index to Action if integer was passed
        action_obj: Action = index_to_action(action) if isinstance(action, int) else action

        # Execute step in simulator
        step_result = self.env.step(action_obj, acting_player=acting_player)

        terminated = step_result.terminated
        truncated = step_result.truncated
        done = terminated or truncated

        winner = self.env.winner

        # Sparse terminal rewards
        # Intermediate steps: reward = 0.0
        # Terminal step: +1.0 if acting player won, -1.0 if acting player lost
        player_rewards: Dict[int, float] = {}
        if done:
            if terminated and winner is not None:
                step_reward = 1.0 if acting_player == winner else -1.0
                for p in range(self.num_players):
                    player_rewards[p] = 1.0 if p == winner else -1.0
            else:
                # Truncation: no winner, all seats penalized for stall
                step_reward = -1.0
                for p in range(self.num_players):
                    player_rewards[p] = -1.0
        else:
            step_reward = 0.0
            for p in range(self.num_players):
                player_rewards[p] = 0.0

        next_obs = step_result.observation
        self._last_obs = next_obs

        # Compile info dictionary
        next_player = step_result.next_player
        info: Dict[str, Any] = {
            "acting_player": acting_player,
            "next_player": next_player,
            "winner": winner,
            "terminated": terminated,
            "truncated": truncated,
            "player_rewards": player_rewards,
            "action_mask": self.env.action_mask(next_player if not done else acting_player),
            "turn_count": self.env.state.turn_count,
            "timestep": self.env.state.timestep,
        }

        return next_obs, step_reward, done, info
