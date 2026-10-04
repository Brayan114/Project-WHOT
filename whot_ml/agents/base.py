"""Abstract Agent base class for WHOT-ML (P0-D4, P0-D5)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from whot_ml.action import Action
from whot_ml.observation import PlayerObservation


class Agent(ABC):
    """Abstract base class for all WHOT-ML decision-making agents."""

    def __init__(self, name: str = "Agent") -> None:
        self.name = name
        self.player_id: Optional[int] = None

    def reset(self, player_id: int, seed: Optional[int] = None) -> None:
        """Initialize or reset agent state before an episode."""
        self.player_id = player_id

    @abstractmethod
    def act(self, observation: PlayerObservation) -> Action:
        """Select a legal Action given the player's legitimate observation.

        Must never access GameState or hidden information.
        """
        pass
