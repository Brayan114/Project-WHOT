"""Configurable Ruleset architecture for WHOT-ML (P0-D1, P0-D3, P0-D4)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from whot_ml.card import BASELINE_VALUE_EFFECTS, Shape, SpecialEffect


class TurnDirection(str, Enum):
    """Direction of play (P0-D1 Section 3, P0-D4 Section 11)."""
    CLOCKWISE = "CLOCKWISE"
    COUNTER_CLOCKWISE = "COUNTER_CLOCKWISE"


class StarterPolicy(str, Enum):
    """How the first acting player is chosen during setup (P0-D4 Section 8)."""
    RANDOM = "RANDOM"
    FIXED_PLAYER_0 = "FIXED_PLAYER_0"


class StackingMode(str, Enum):
    """Stacking rules for Pick Two and Pick Three (P0-D4 Section 20)."""
    NO_STACKING = "NO_STACKING"
    SAME_EFFECT = "SAME_EFFECT"      # Baseline: 2 stacks with 2, 5 stacks with 5
    ANY_PICK_CARD = "ANY_PICK_CARD"  # 2 and 5 can cross-stack


class FinalCardOnePolicy(str, Enum):
    """How the prohibition of Card 1 as final winning card is enforced."""
    REJECT_LEGALITY = "REJECT_LEGALITY"       # Baseline: Playing 1 is illegal if hand_size == 1
    PLAY_WITH_PENALTY = "PLAY_WITH_PENALTY"   # 1 can be played, but extra turn cannot win; penalty applied


class MarketExhaustionPolicy(str, Enum):
    """Behavior when draw pile is exhausted (P0-D1 Section 16, P0-D4 Section 16)."""
    PRESERVE_TOP_AND_RESHUFFLE_DISCARD = "PRESERVE_TOP_AND_RESHUFFLE_DISCARD"
    TERMINATE_DRAW_UNAVAILABLE = "TERMINATE_DRAW_UNAVAILABLE"


class InitialCardPolicy(str, Enum):
    """Behavior for the starting face-up card (P0-D4 Section 9)."""
    NO_EFFECT_START = "NO_EFFECT_START"          # Baseline: card placed, special effects do not trigger
    ACTIVATE_SPECIAL_EFFECT = "ACTIVATE_SPECIAL_EFFECT"


class LastCardViolationPenalty(str, Enum):
    """Penalty for undeclared attempted victory (P0-D1 Section 13, P0-D4 Section 26)."""
    DRAW_1 = "DRAW_1"  # Baseline: draw 1 card
    DRAW_2 = "DRAW_2"


@dataclass(frozen=True)
class WHOTConfig:
    """Complete, serializable configuration of all WHOT rules and parameters.

    Every gameplay decision affecting mechanics, legality, turn transitions,
    penalties, declarations, and terminal conditions is governed by this configuration.
    """
    ruleset_name: str = "WHOT-NG-v1"
    player_count: int = 4
    starting_hand_size: int = 6
    turn_direction: TurnDirection = TurnDirection.CLOCKWISE
    starter_policy: StarterPolicy = StarterPolicy.RANDOM

    # Special card effect assignments (value -> SpecialEffect)
    special_card_mapping: Dict[int, SpecialEffect] = field(
        default_factory=lambda: dict(BASELINE_VALUE_EFFECTS)
    )

    # Pick Two (Card 2) configuration
    pick_two_enabled: bool = True
    pick_two_stacking: StackingMode = StackingMode.SAME_EFFECT

    # Pick Three (Card 5) configuration
    pick_three_enabled: bool = True
    pick_three_stacking: StackingMode = StackingMode.SAME_EFFECT

    # Penalty defense obligations
    penalty_defense_mandatory: bool = False  # If False, player may defend or draw accumulated penalty
    whot_defends_penalty: bool = False       # Baseline: WHOT cannot defend an active pick penalty

    # WHOT wild configuration
    whot_shape_selection_options: Tuple[Shape, ...] = field(
        default_factory=Shape.ordinary_shapes
    )

    # Other special card switches
    hold_on_enabled: bool = True
    suspension_enabled: bool = True
    general_market_enabled: bool = True

    # Last-card declaration configuration
    last_card_declaration_enabled: bool = True
    declaration_advances_turn: bool = False  # Baseline: declaration does not consume the turn
    last_card_violation_penalty: LastCardViolationPenalty = LastCardViolationPenalty.DRAW_1

    # Final-card restrictions
    final_card_one_policy: FinalCardOnePolicy = FinalCardOnePolicy.REJECT_LEGALITY
    final_special_cards_allowed: bool = True  # Baseline: 2, 5, 8, 14, 20 can win if declared

    # Drawing policies
    draw_policy: str = "DRAW_ONE_IF_NO_LEGAL"  # DRAW is illegal if legal playable cards exist
    drawn_card_immediate_play: bool = False    # Baseline: drawn card cannot immediately be played

    # Market policies
    market_exhaustion_policy: MarketExhaustionPolicy = (
        MarketExhaustionPolicy.PRESERVE_TOP_AND_RESHUFFLE_DISCARD
    )
    initial_card_policy: InitialCardPolicy = InitialCardPolicy.NO_EFFECT_START
    initial_whot_selection_policy: str = "UNIFORM_RANDOM"

    # Terminal & Scoring policies
    scoring_policy: str = "ZERO_SUM_WINNER_PLUS_1_LOSERS_MINUS_1"
    maximum_turns: int = 1000

    # Operational
    debug_mode: bool = True

    def __post_init__(self) -> None:
        if not (2 <= self.player_count <= 6):
            raise ValueError(f"player_count must be in [2, 6], got {self.player_count}")
        if self.starting_hand_size < 1:
            raise ValueError(f"starting_hand_size must be >= 1, got {self.starting_hand_size}")
        if self.player_count * self.starting_hand_size >= 54:
            raise ValueError(
                f"Cannot deal {self.player_count * self.starting_hand_size} cards from a 54-card deck"
            )
        if self.maximum_turns < 10:
            raise ValueError("maximum_turns must be at least 10")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a JSON-serializable dictionary."""
        d = asdict(self)
        d["turn_direction"] = self.turn_direction.value
        d["starter_policy"] = self.starter_policy.value
        d["special_card_mapping"] = {
            str(k): (v.value if isinstance(v, SpecialEffect) else v)
            for k, v in self.special_card_mapping.items()
        }
        d["pick_two_stacking"] = self.pick_two_stacking.value
        d["pick_three_stacking"] = self.pick_three_stacking.value
        d["whot_shape_selection_options"] = [
            s.value if isinstance(s, Shape) else s
            for s in self.whot_shape_selection_options
        ]
        d["last_card_violation_penalty"] = self.last_card_violation_penalty.value
        d["final_card_one_policy"] = self.final_card_one_policy.value
        d["market_exhaustion_policy"] = self.market_exhaustion_policy.value
        d["initial_card_policy"] = self.initial_card_policy.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WHOTConfig:
        """Reconstruct configuration from a dictionary."""
        d = dict(data)
        if "turn_direction" in d and isinstance(d["turn_direction"], str):
            d["turn_direction"] = TurnDirection(d["turn_direction"])
        if "starter_policy" in d and isinstance(d["starter_policy"], str):
            d["starter_policy"] = StarterPolicy(d["starter_policy"])
        if "special_card_mapping" in d:
            d["special_card_mapping"] = {
                int(k): SpecialEffect(v) if isinstance(v, str) else v
                for k, v in d["special_card_mapping"].items()
            }
        if "pick_two_stacking" in d and isinstance(d["pick_two_stacking"], str):
            d["pick_two_stacking"] = StackingMode(d["pick_two_stacking"])
        if "pick_three_stacking" in d and isinstance(d["pick_three_stacking"], str):
            d["pick_three_stacking"] = StackingMode(d["pick_three_stacking"])
        if "whot_shape_selection_options" in d:
            d["whot_shape_selection_options"] = tuple(
                Shape(s) if isinstance(s, str) else s
                for s in d["whot_shape_selection_options"]
            )
        if "last_card_violation_penalty" in d and isinstance(d["last_card_violation_penalty"], str):
            d["last_card_violation_penalty"] = LastCardViolationPenalty(d["last_card_violation_penalty"])
        if "final_card_one_policy" in d and isinstance(d["final_card_one_policy"], str):
            d["final_card_one_policy"] = FinalCardOnePolicy(d["final_card_one_policy"])
        if "market_exhaustion_policy" in d and isinstance(d["market_exhaustion_policy"], str):
            d["market_exhaustion_policy"] = MarketExhaustionPolicy(d["market_exhaustion_policy"])
        if "initial_card_policy" in d and isinstance(d["initial_card_policy"], str):
            d["initial_card_policy"] = InitialCardPolicy(d["initial_card_policy"])

        return cls(**d)


def get_baseline_config() -> WHOTConfig:
    """Return the reference WHOT-NG-v1 baseline configuration."""
    return WHOTConfig()
