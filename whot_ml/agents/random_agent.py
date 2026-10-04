"""Random Legal Agent baseline for WHOT-ML (P0-D5 Section 11.2)."""

from __future__ import annotations

import random
from typing import Optional

from whot_ml.action import Action
from whot_ml.agents.base import Agent
from whot_ml.observation import PlayerObservation


class RandomLegalAgent(Agent):
    """Selects uniformly at random among currently legal actions.

    Adheres strictly to the action mask and never knowingly selects an illegal action.
    """

    def __init__(self, name: str = "RandomLegalAgent", seed: Optional[int] = None) -> None:
        super().__init__(name=name)
        self._rng = random.Random(seed)

    def reset(self, player_id: int, seed: Optional[int] = None) -> None:
        super().reset(player_id, seed)
        if seed is not None:
            self._rng.seed(seed)

    def act(self, observation: PlayerObservation) -> Action:
        legal_actions = observation.legal_actions
        if not legal_actions:
            raise RuntimeError(f"Agent {self.name} received observation with no legal actions")
        return self._rng.choice(legal_actions)
