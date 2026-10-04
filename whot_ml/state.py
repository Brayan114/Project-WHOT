"""Complete internal GameState model for WHOT-ML (P0-D2, P0-D4)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from whot_ml.card import (
    CANONICAL_CARD_BY_ID,
    CANONICAL_CARD_BY_INDEX,
    CANONICAL_DECK,
    Card,
    Shape,
    SpecialEffect,
)
from whot_ml.invariants import InvariantValidator
from whot_ml.rng_manager import RNGManager
from whot_ml.ruleset import (
    InitialCardPolicy,
    StarterPolicy,
    TurnDirection,
    WHOTConfig,
    get_baseline_config,
)
from whot_ml.turn_manager import TurnModifier


@dataclass
class GameState:
    """The full, ground-truth internal state of the WHOT-ML simulator.

    Contains complete hidden information (all hands, market order, RNG state)
    accessible only to the simulator and validation systems. Never exposed
    directly to player agents.
    """
    config: WHOTConfig
    hands: Dict[int, List[Card]]
    market: List[Card]
    play_pile: List[Card]
    current_call: Shape
    current_player: int
    turn_direction: TurnDirection = TurnDirection.CLOCKWISE
    active_penalty_type: Optional[SpecialEffect] = None
    active_penalty_count: int = 0
    turn_modifier: TurnModifier = TurnModifier.NORMAL
    last_card_declared: Dict[int, bool] = field(default_factory=dict)
    timestep: int = 0
    turn_count: int = 0
    episode_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rng_manager: RNGManager = field(default_factory=RNGManager)
    is_terminal: bool = False
    winner: Optional[int] = None

    @property
    def top_card(self) -> Card:
        """The currently visible top card on the public play pile."""
        if not self.play_pile:
            raise IndexError("Play pile is empty")
        return self.play_pile[-1]

    @property
    def has_active_penalty(self) -> bool:
        """Return True if there is an unresolved Pick Two or Pick Three penalty."""
        return self.active_penalty_count > 0 and self.active_penalty_type is not None

    def player_hand(self, player_id: int) -> List[Card]:
        """Return the current list of physical cards held by a player."""
        if player_id not in self.hands:
            raise KeyError(f"Player {player_id} not in game state")
        return self.hands[player_id]

    def player_hand_size(self, player_id: int) -> int:
        """Return the count of cards held by a player."""
        return len(self.hands[player_id])

    @classmethod
    def create_initial_state(
        cls,
        config: Optional[WHOTConfig] = None,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
    ) -> GameState:
        """Construct, deal, and initialize a complete ground-truth GameState.

        Follows P0-D4 Section 7 & 8:
          1. Initialize seeded RNG.
          2. Shuffle the canonical 54 physical cards.
          3. Deal starting hands in round-robin order.
          4. Establish the starting face-up card in the play pile.
          5. Remaining cards become the face-down market.
          6. Select starting player according to starter policy.
          7. Establish initial call according to initial card policy.
          8. Validate invariants.
        """
        cfg = config if config is not None else get_baseline_config()
        rng = RNGManager(seed)
        ep_id = episode_id if episode_id is not None else str(uuid.uuid4())

        # 1. Prepare deck
        deck: List[Card] = list(CANONICAL_DECK)
        rng.shuffle(deck)

        # 2. Deal hands
        hands: Dict[int, List[Card]] = {p: [] for p in range(cfg.player_count)}
        for _ in range(cfg.starting_hand_size):
            for p in range(cfg.player_count):
                hands[p].append(deck.pop())

        # 3. Starting play card
        starting_card = deck.pop()
        play_pile: List[Card] = [starting_card]

        # 4. Remaining cards become market
        market: List[Card] = deck

        # 5. Starting player
        if cfg.starter_policy == StarterPolicy.FIXED_PLAYER_0:
            current_player = 0
        else:
            current_player = rng.choice(list(range(cfg.player_count)))

        # 6. Initial call
        if cfg.initial_card_policy == InitialCardPolicy.NO_EFFECT_START:
            if starting_card.is_whot:
                current_call = rng.choice(list(Shape.ordinary_shapes()))
            else:
                current_call = starting_card.shape
        else:
            current_call = starting_card.shape if not starting_card.is_whot else rng.choice(list(Shape.ordinary_shapes()))

        last_card_declared = {p: False for p in range(cfg.player_count)}

        state = cls(
            config=cfg,
            hands=hands,
            market=market,
            play_pile=play_pile,
            current_call=current_call,
            current_player=current_player,
            turn_direction=cfg.turn_direction,
            active_penalty_type=None,
            active_penalty_count=0,
            turn_modifier=TurnModifier.NORMAL,
            last_card_declared=last_card_declared,
            timestep=0,
            turn_count=0,
            episode_id=ep_id,
            rng_manager=rng,
            is_terminal=False,
            winner=None,
        )

        if cfg.debug_mode:
            InvariantValidator.validate(state)

        return state
