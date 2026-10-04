"""Unit tests for Ruleset configuration and serialization (P0-D1, P0-D4)."""

import pytest
from whot_ml.card import Shape, SpecialEffect
from whot_ml.ruleset import (
    FinalCardOnePolicy,
    InitialCardPolicy,
    LastCardViolationPenalty,
    MarketExhaustionPolicy,
    StackingMode,
    StarterPolicy,
    TurnDirection,
    WHOTConfig,
    get_baseline_config,
)


def test_baseline_config_defaults():
    """Verify WHOT-NG-v1 baseline configuration parameters match specifications."""
    config = get_baseline_config()

    assert config.ruleset_name == "WHOT-NG-v1"
    assert config.player_count == 4
    assert config.starting_hand_size == 6
    assert config.turn_direction == TurnDirection.CLOCKWISE
    assert config.starter_policy == StarterPolicy.RANDOM

    # Stacking
    assert config.pick_two_enabled is True
    assert config.pick_two_stacking == StackingMode.SAME_EFFECT
    assert config.pick_three_enabled is True
    assert config.pick_three_stacking == StackingMode.SAME_EFFECT

    # Penalty & WHOT
    assert config.penalty_defense_mandatory is False
    assert config.whot_defends_penalty is False

    # Declarations
    assert config.last_card_declaration_enabled is True
    assert config.declaration_advances_turn is False
    assert config.last_card_violation_penalty == LastCardViolationPenalty.DRAW_1

    # Final card 1 policy
    assert config.final_card_one_policy == FinalCardOnePolicy.REJECT_LEGALITY
    assert config.final_special_cards_allowed is True

    # Market
    assert config.market_exhaustion_policy == MarketExhaustionPolicy.PRESERVE_TOP_AND_RESHUFFLE_DISCARD
    assert config.initial_card_policy == InitialCardPolicy.NO_EFFECT_START
    assert config.drawn_card_immediate_play is False


def test_config_serialization_round_trip():
    """Verify WHOTConfig serializes to dict and reconstructs identically."""
    config = get_baseline_config()
    d = config.to_dict()
    restored = WHOTConfig.from_dict(d)

    assert restored == config
    assert restored.turn_direction == TurnDirection.CLOCKWISE
    assert restored.pick_two_stacking == StackingMode.SAME_EFFECT
    assert restored.special_card_mapping[1] == SpecialEffect.HOLD_ON


def test_custom_rule_configurations():
    """Verify ruleset can be customized without altering default baseline."""
    custom = WHOTConfig(
        ruleset_name="WHOT-VARIANT-TEST",
        player_count=2,
        starting_hand_size=5,
        turn_direction=TurnDirection.COUNTER_CLOCKWISE,
        pick_two_stacking=StackingMode.ANY_PICK_CARD,
        penalty_defense_mandatory=True,
        declaration_advances_turn=True,
    )

    assert custom.ruleset_name == "WHOT-VARIANT-TEST"
    assert custom.player_count == 2
    assert custom.starting_hand_size == 5
    assert custom.turn_direction == TurnDirection.COUNTER_CLOCKWISE
    assert custom.pick_two_stacking == StackingMode.ANY_PICK_CARD
    assert custom.penalty_defense_mandatory is True
    assert custom.declaration_advances_turn is True

    # Round trip
    d = custom.to_dict()
    restored = WHOTConfig.from_dict(d)
    assert restored == custom


def test_invalid_configurations_raise_errors():
    """Verify invalid configurations are rejected during validation."""
    with pytest.raises(ValueError):
        WHOTConfig(player_count=1)  # Minimum 2

    with pytest.raises(ValueError):
        WHOTConfig(player_count=7)  # Maximum 6

    with pytest.raises(ValueError):
        WHOTConfig(starting_hand_size=0)

    with pytest.raises(ValueError):
        # 6 players x 9 cards = 54 dealt cards leaves 0 for market/initial card
        WHOTConfig(player_count=6, starting_hand_size=9)
