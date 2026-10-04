"""Rule-Based Agent baseline for WHOT-ML (P0-D5 Section 11.3)."""

from __future__ import annotations

import random
from collections import Counter
from typing import Dict, List, Optional

from whot_ml.action import Action, ActionType
from whot_ml.agents.base import Agent
from whot_ml.card import Shape, SpecialEffect
from whot_ml.observation import PlayerObservation


class RuleBasedAgent(Agent):
    """Transparent heuristic agent that uses only legitimate PlayerObservation.

    Heuristic Priorities:
      1. Always declare last card when DECLARE_LAST is available.
      2. If an active penalty exists, prioritize playing a legal defense over drawing.
      3. Prefer action cards (Hold On 1, General Market 14, Suspension 8, Pick 2/5).
      4. Prefer ordinary cards over WHOT to preserve wildcards for emergencies.
      5. When playing WHOT, select the ordinary shape most frequent in own hand.
      6. Fall back to remaining legal plays or DRAW.
    """

    def __init__(self, name: str = "RuleBasedAgent", seed: Optional[int] = None) -> None:
        super().__init__(name=name)
        self._rng = random.Random(seed)

    def reset(self, player_id: int, seed: Optional[int] = None) -> None:
        super().reset(player_id, seed)
        if seed is not None:
            self._rng.seed(seed)

    def act(self, observation: PlayerObservation) -> Action:
        legal = observation.legal_actions
        if not legal:
            raise RuntimeError(f"Agent {self.name} received observation with no legal actions")

        # 1. Declaration priority: always declare if hand size is 1 and undeclared
        declares = [a for a in legal if a.action_type == ActionType.DECLARE_LAST]
        if declares:
            return declares[0]

        # 2. Defend against active penalties if possible
        if observation.active_penalty_count > 0:
            defending_plays = [a for a in legal if a.action_type in (ActionType.PLAY, ActionType.PLAY_WHOT)]
            if defending_plays:
                return defending_plays[0]
            # Fall back to DRAW if no defense exists
            draw_actions = [a for a in legal if a.action_type == ActionType.DRAW]
            if draw_actions:
                return draw_actions[0]

        # 3. Separate ordinary plays and WHOT plays
        ordinary_plays = [a for a in legal if a.action_type == ActionType.PLAY]
        whot_plays = [a for a in legal if a.action_type == ActionType.PLAY_WHOT]

        # 4. If ordinary plays exist, prefer high-impact special cards
        if ordinary_plays:
            card_map = {c.id: c for c in observation.hand}

            # Group ordinary plays by card value
            hold_ons = [a for a in ordinary_plays if card_map.get(a.card_id) and card_map[a.card_id].value == 1]
            if hold_ons:
                return hold_ons[0]

            general_markets = [
                a for a in ordinary_plays if card_map.get(a.card_id) and card_map[a.card_id].value == 14
            ]
            if general_markets:
                return general_markets[0]

            suspensions = [
                a for a in ordinary_plays if card_map.get(a.card_id) and card_map[a.card_id].value == 8
            ]
            if suspensions:
                return suspensions[0]

            attacks = [
                a for a in ordinary_plays if card_map.get(a.card_id) and card_map[a.card_id].value in (2, 5)
            ]
            if attacks:
                return attacks[0]

            # Otherwise play the first ordinary card
            return ordinary_plays[0]

        # 5. If only WHOT plays exist (or preferred), choose shape strategically
        if whot_plays:
            # Count shapes in own hand excluding WHOT
            ordinary_cards = [c for c in observation.hand if c.shape.is_ordinary]
            if ordinary_cards:
                shape_counts = Counter(c.shape for c in ordinary_cards)
                preferred_shape, _ = shape_counts.most_common(1)[0]
            else:
                preferred_shape = Shape.CIRCLE

            matching_whots = [a for a in whot_plays if a.selected_shape == preferred_shape]
            if matching_whots:
                return matching_whots[0]
            return whot_plays[0]

        # 6. Must be DRAW
        return legal[0]
