"""Regression tests for StackingMode behavior under active penalties (v1.0.1).

Validates all three stacking modes:
1. NO_STACKING: No defensive card may be played; the affected player must DRAW.
2. SAME_EFFECT: Only matching penalty card defends (2 defends 2, 5 defends 5).
3. ANY_PICK_CARD: Cross-stacking allowed (2 or 5 defends against either penalty).
"""

import pytest

from whot_ml.action import ACTION_INDEX_DRAW, ActionType
from whot_ml.card import CANONICAL_CARD_BY_ID, Shape, SpecialEffect
from whot_ml.rules_engine import RulesEngine
from whot_ml.ruleset import StackingMode, WHOTConfig, get_baseline_config
from whot_ml.state import GameState


def test_no_stacking_rejects_pick_two_defense():
    """Verify that with pick_two_stacking=NO_STACKING, holding Card 2 is not a legal defense."""
    cfg = WHOTConfig(pick_two_stacking=StackingMode.NO_STACKING)
    state = GameState.create_initial_state(config=cfg, seed=123)
    p = state.current_player

    two_card = CANONICAL_CARD_BY_ID["TRIANGLE_2"]
    top_card = CANONICAL_CARD_BY_ID["CIRCLE_2"]

    # is_card_playable check
    playable = RulesEngine.is_card_playable(
        card=two_card,
        top_card=top_card,
        current_call=Shape.CIRCLE,
        active_penalty_type=SpecialEffect.PICK_TWO,
        active_penalty_count=2,
        hand_size=5,
        config=cfg,
    )
    assert playable is False

    # legal_actions check
    state.active_penalty_type = SpecialEffect.PICK_TWO
    state.active_penalty_count = 2
    state.play_pile = [top_card]
    state.current_call = Shape.CIRCLE
    state.hands[p] = [two_card]

    actions = RulesEngine.legal_actions(state)
    played_card_ids = [a.card_id for a in actions if a.card_id is not None]
    assert "TRIANGLE_2" not in played_card_ids


def test_no_stacking_rejects_pick_three_defense():
    """Verify that with pick_three_stacking=NO_STACKING, holding Card 5 is not a legal defense."""
    cfg = WHOTConfig(pick_three_stacking=StackingMode.NO_STACKING)
    state = GameState.create_initial_state(config=cfg, seed=123)
    p = state.current_player

    five_card = CANONICAL_CARD_BY_ID["STAR_5"]
    top_card = CANONICAL_CARD_BY_ID["CIRCLE_5"]

    playable = RulesEngine.is_card_playable(
        card=five_card,
        top_card=top_card,
        current_call=Shape.CIRCLE,
        active_penalty_type=SpecialEffect.PICK_THREE,
        active_penalty_count=3,
        hand_size=5,
        config=cfg,
    )
    assert playable is False

    state.active_penalty_type = SpecialEffect.PICK_THREE
    state.active_penalty_count = 3
    state.play_pile = [top_card]
    state.current_call = Shape.CIRCLE
    state.hands[p] = [five_card]

    actions = RulesEngine.legal_actions(state)
    played_card_ids = [a.card_id for a in actions if a.card_id is not None]
    assert "STAR_5" not in played_card_ids


def test_no_stacking_requires_draw():
    """Verify that under NO_STACKING, DRAW is the only legal action when facing active penalty."""
    cfg = WHOTConfig(
        pick_two_stacking=StackingMode.NO_STACKING,
        pick_three_stacking=StackingMode.NO_STACKING,
    )
    state = GameState.create_initial_state(config=cfg, seed=123)
    p = state.current_player

    # Player holds both Card 2 and Card 5 and normal matching cards
    state.active_penalty_type = SpecialEffect.PICK_TWO
    state.active_penalty_count = 2
    state.play_pile = [CANONICAL_CARD_BY_ID["CIRCLE_2"]]
    state.current_call = Shape.CIRCLE
    state.hands[p] = [
        CANONICAL_CARD_BY_ID["TRIANGLE_2"],
        CANONICAL_CARD_BY_ID["STAR_5"],
        CANONICAL_CARD_BY_ID["CIRCLE_7"],
    ]

    actions = RulesEngine.legal_actions(state)
    assert len(actions) == 1
    assert actions[0].action_type == ActionType.DRAW

    mask = RulesEngine.action_mask(state)
    assert mask[ACTION_INDEX_DRAW] == 1
    assert sum(mask) == 1


def test_same_effect_unchanged():
    """Verify that baseline SAME_EFFECT preserves exact v1.0.0 behavior."""
    cfg = get_baseline_config()
    assert cfg.pick_two_stacking == StackingMode.SAME_EFFECT
    assert cfg.pick_three_stacking == StackingMode.SAME_EFFECT

    two_card = CANONICAL_CARD_BY_ID["CROSS_2"]
    five_card = CANONICAL_CARD_BY_ID["CROSS_5"]
    ordinary_card = CANONICAL_CARD_BY_ID["CROSS_7"]
    top_two = CANONICAL_CARD_BY_ID["CIRCLE_2"]
    top_five = CANONICAL_CARD_BY_ID["CIRCLE_5"]

    # Active PICK_TWO: 2 defends, 5 does not, 7 does not
    assert RulesEngine.is_card_playable(
        card=two_card, top_card=top_two, current_call=Shape.CIRCLE,
        active_penalty_type=SpecialEffect.PICK_TWO, active_penalty_count=2,
        hand_size=5, config=cfg,
    ) is True

    assert RulesEngine.is_card_playable(
        card=five_card, top_card=top_two, current_call=Shape.CIRCLE,
        active_penalty_type=SpecialEffect.PICK_TWO, active_penalty_count=2,
        hand_size=5, config=cfg,
    ) is False

    assert RulesEngine.is_card_playable(
        card=ordinary_card, top_card=top_two, current_call=Shape.CIRCLE,
        active_penalty_type=SpecialEffect.PICK_TWO, active_penalty_count=2,
        hand_size=5, config=cfg,
    ) is False

    # Active PICK_THREE: 5 defends, 2 does not, 7 does not
    assert RulesEngine.is_card_playable(
        card=five_card, top_card=top_five, current_call=Shape.CIRCLE,
        active_penalty_type=SpecialEffect.PICK_THREE, active_penalty_count=3,
        hand_size=5, config=cfg,
    ) is True

    assert RulesEngine.is_card_playable(
        card=two_card, top_card=top_five, current_call=Shape.CIRCLE,
        active_penalty_type=SpecialEffect.PICK_THREE, active_penalty_count=3,
        hand_size=5, config=cfg,
    ) is False

    assert RulesEngine.is_card_playable(
        card=ordinary_card, top_card=top_five, current_call=Shape.CIRCLE,
        active_penalty_type=SpecialEffect.PICK_THREE, active_penalty_count=3,
        hand_size=5, config=cfg,
    ) is False


def test_any_pick_card_cross_stacks():
    """Verify that ANY_PICK_CARD allows Card 5 to defend Pick Two and Card 2 to defend Pick Three."""
    cfg = WHOTConfig(
        pick_two_stacking=StackingMode.ANY_PICK_CARD,
        pick_three_stacking=StackingMode.ANY_PICK_CARD,
    )

    two_card = CANONICAL_CARD_BY_ID["SQUARE_2"]
    five_card = CANONICAL_CARD_BY_ID["STAR_5"]
    ordinary_card = CANONICAL_CARD_BY_ID["CIRCLE_8"]

    # Active PICK_TWO: both 2 and 5 defend
    assert RulesEngine.is_card_playable(
        card=two_card, top_card=CANONICAL_CARD_BY_ID["CIRCLE_2"], current_call=Shape.CIRCLE,
        active_penalty_type=SpecialEffect.PICK_TWO, active_penalty_count=2,
        hand_size=5, config=cfg,
    ) is True

    assert RulesEngine.is_card_playable(
        card=five_card, top_card=CANONICAL_CARD_BY_ID["CIRCLE_2"], current_call=Shape.CIRCLE,
        active_penalty_type=SpecialEffect.PICK_TWO, active_penalty_count=2,
        hand_size=5, config=cfg,
    ) is True

    assert RulesEngine.is_card_playable(
        card=ordinary_card, top_card=CANONICAL_CARD_BY_ID["CIRCLE_2"], current_call=Shape.CIRCLE,
        active_penalty_type=SpecialEffect.PICK_TWO, active_penalty_count=2,
        hand_size=5, config=cfg,
    ) is False

    # Active PICK_THREE: both 5 and 2 defend
    assert RulesEngine.is_card_playable(
        card=five_card, top_card=CANONICAL_CARD_BY_ID["CIRCLE_5"], current_call=Shape.CIRCLE,
        active_penalty_type=SpecialEffect.PICK_THREE, active_penalty_count=3,
        hand_size=5, config=cfg,
    ) is True

    assert RulesEngine.is_card_playable(
        card=two_card, top_card=CANONICAL_CARD_BY_ID["CIRCLE_5"], current_call=Shape.CIRCLE,
        active_penalty_type=SpecialEffect.PICK_THREE, active_penalty_count=3,
        hand_size=5, config=cfg,
    ) is True

    assert RulesEngine.is_card_playable(
        card=ordinary_card, top_card=CANONICAL_CARD_BY_ID["CIRCLE_5"], current_call=Shape.CIRCLE,
        active_penalty_type=SpecialEffect.PICK_THREE, active_penalty_count=3,
        hand_size=5, config=cfg,
    ) is False
