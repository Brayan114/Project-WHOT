"""Unit tests for RulesEngine, action legality, DRAW restriction, and action masking."""

import pytest
from whot_ml.action import (
    ACTION_INDEX_DECLARE_LAST,
    ACTION_INDEX_DRAW,
    ActionType,
    index_to_action,
)
from whot_ml.card import (
    CANONICAL_CARD_BY_ID,
    Card,
    CardType,
    Shape,
    SpecialEffect,
)
from whot_ml.rules_engine import IllegalActionError, RulesEngine
from whot_ml.ruleset import FinalCardOnePolicy, WHOTConfig, get_baseline_config
from whot_ml.state import GameState


def test_normal_card_matching():
    """Verify shape matching, value matching, and WHOT wild behavior."""
    cfg = get_baseline_config()
    top_card = CANONICAL_CARD_BY_ID["CIRCLE_7"]
    current_call = Shape.CIRCLE

    # Same shape, different value -> playable
    c_same_shape = CANONICAL_CARD_BY_ID["CIRCLE_3"]
    assert RulesEngine.is_card_playable(
        card=c_same_shape,
        top_card=top_card,
        current_call=current_call,
        active_penalty_type=None,
        active_penalty_count=0,
        hand_size=4,
        config=cfg,
    ) is True

    # Same value, different shape -> playable
    c_same_value = CANONICAL_CARD_BY_ID["STAR_7"]
    assert RulesEngine.is_card_playable(
        card=c_same_value,
        top_card=top_card,
        current_call=current_call,
        active_penalty_type=None,
        active_penalty_count=0,
        hand_size=4,
        config=cfg,
    ) is True

    # Different shape and different value -> NOT playable
    c_different = CANONICAL_CARD_BY_ID["CROSS_10"]
    assert RulesEngine.is_card_playable(
        card=c_different,
        top_card=top_card,
        current_call=current_call,
        active_penalty_type=None,
        active_penalty_count=0,
        hand_size=4,
        config=cfg,
    ) is False

    # WHOT is wild -> playable
    whot_card = CANONICAL_CARD_BY_ID["WHOT_1"]
    assert RulesEngine.is_card_playable(
        card=whot_card,
        top_card=top_card,
        current_call=current_call,
        active_penalty_type=None,
        active_penalty_count=0,
        hand_size=4,
        config=cfg,
    ) is True


def test_draw_is_illegal_when_playable_card_exists():
    """Verify requirement: DRAW must be illegal if player has at least one legal playable card."""
    state = GameState.create_initial_state(seed=42)
    p = state.current_player

    # Give player an explicitly matching card
    matching_card = CANONICAL_CARD_BY_ID["CIRCLE_3"]
    state.play_pile = [CANONICAL_CARD_BY_ID["CIRCLE_7"]]
    state.current_call = Shape.CIRCLE
    state.hands[p] = [matching_card]

    actions = RulesEngine.legal_actions(state)
    action_types = [a.action_type for a in actions]
    mask = RulesEngine.action_mask(state)

    # Play action must be present, DRAW action (74) must be strictly absent
    assert ActionType.PLAY in action_types
    assert ActionType.DRAW not in action_types
    assert mask[ACTION_INDEX_DRAW] == 0


def test_draw_becomes_available_when_no_playable_card_exists():
    """Verify requirement: DRAW is the only normal card action when no card matches."""
    state = GameState.create_initial_state(seed=42)
    p = state.current_player

    # Top card is Circle 7, Call is Circle
    state.play_pile = [CANONICAL_CARD_BY_ID["CIRCLE_7"]]
    state.current_call = Shape.CIRCLE

    # Give player only unplayable cards (Triangle 10, Square 11)
    unplayable_1 = CANONICAL_CARD_BY_ID["TRIANGLE_10"]
    unplayable_2 = CANONICAL_CARD_BY_ID["SQUARE_11"]
    state.hands[p] = [unplayable_1, unplayable_2]

    actions = RulesEngine.legal_actions(state)
    mask = RulesEngine.action_mask(state)

    assert len(actions) == 1
    assert actions[0].action_type == ActionType.DRAW
    assert mask[ACTION_INDEX_DRAW] == 1


def test_final_card_one_restriction():
    """Verify requirement: Card 1 (Hold On) cannot be played as the winning final card."""
    state = GameState.create_initial_state(seed=42)
    p = state.current_player

    # Top card is Circle 7, call is Circle
    state.play_pile = [CANONICAL_CARD_BY_ID["CIRCLE_7"]]
    state.current_call = Shape.CIRCLE

    # Player has only Circle 1 in hand (hand_size == 1)
    card_1 = CANONICAL_CARD_BY_ID["CIRCLE_1"]
    state.hands[p] = [card_1]
    state.last_card_declared[p] = True  # Already declared

    actions = RulesEngine.legal_actions(state)
    action_types = [a.action_type for a in actions]

    # Under REJECT_LEGALITY, Card 1 cannot be played. With no other playable cards, player must DRAW!
    assert ActionType.PLAY not in action_types
    assert ActionType.DRAW in action_types

    # But if hand has 2 cards (hand_size > 1), Card 1 is legal
    state.hands[p] = [card_1, CANONICAL_CARD_BY_ID["SQUARE_11"]]
    actions_2 = RulesEngine.legal_actions(state)
    assert any(a.action_type == ActionType.PLAY and a.card_id == "CIRCLE_1" for a in actions_2)


def test_pick_two_penalty_defense_and_whot_restriction():
    """Verify Pick Two penalty rules: only 2 can defend; WHOT cannot defend."""
    state = GameState.create_initial_state(seed=42)
    p = state.current_player

    state.active_penalty_type = SpecialEffect.PICK_TWO
    state.active_penalty_count = 2
    state.play_pile = [CANONICAL_CARD_BY_ID["CIRCLE_2"]]
    state.current_call = Shape.CIRCLE

    # Player has: Triangle 2 (defense), Circle 4 (matches shape but not defense), WHOT (wild but cannot defend)
    two_card = CANONICAL_CARD_BY_ID["TRIANGLE_2"]
    matching_ordinary = CANONICAL_CARD_BY_ID["CIRCLE_4"]
    whot_card = CANONICAL_CARD_BY_ID["WHOT_1"]

    state.hands[p] = [two_card, matching_ordinary, whot_card]

    actions = RulesEngine.legal_actions(state)
    played_card_ids = [a.card_id for a in actions if a.card_id is not None]

    # Only TRIANGLE_2 is a legal defense
    assert "TRIANGLE_2" in played_card_ids
    assert "CIRCLE_4" not in played_card_ids
    assert "WHOT_1" not in played_card_ids

    # With default penalty_defense_mandatory=False, player can also choose DRAW (to take the penalty)
    assert any(a.action_type == ActionType.DRAW for a in actions)


def test_pick_two_mandatory_defense():
    """Verify penalty_defense_mandatory=True forces defending play over DRAW."""
    cfg_mandatory = WHOTConfig(penalty_defense_mandatory=True)
    state = GameState.create_initial_state(config=cfg_mandatory, seed=42)
    p = state.current_player

    state.active_penalty_type = SpecialEffect.PICK_TWO
    state.active_penalty_count = 2
    two_card = CANONICAL_CARD_BY_ID["TRIANGLE_2"]
    state.hands[p] = [two_card]

    actions = RulesEngine.legal_actions(state)
    action_types = [a.action_type for a in actions]

    # DRAW is illegal because defense is mandatory and player holds a 2
    assert ActionType.PLAY in action_types
    assert ActionType.DRAW not in action_types


def test_pick_three_penalty_defense():
    """Verify Pick Three penalty is defended only by 5."""
    state = GameState.create_initial_state(seed=42)
    p = state.current_player

    state.active_penalty_type = SpecialEffect.PICK_THREE
    state.active_penalty_count = 3
    state.play_pile = [CANONICAL_CARD_BY_ID["CIRCLE_5"]]
    state.current_call = Shape.CIRCLE

    five_card = CANONICAL_CARD_BY_ID["STAR_5"]
    two_card = CANONICAL_CARD_BY_ID["CIRCLE_2"]
    state.hands[p] = [five_card, two_card]

    actions = RulesEngine.legal_actions(state)
    played_card_ids = [a.card_id for a in actions if a.card_id is not None]

    assert "STAR_5" in played_card_ids
    assert "CIRCLE_2" not in played_card_ids  # Cannot defend Pick 3 with Pick 2 in baseline SAME_EFFECT


def test_declaration_action_legality():
    """Verify DECLARE_LAST is legal only when hand_size == 1 and not yet declared."""
    state = GameState.create_initial_state(seed=42)
    p = state.current_player

    # 1. Hand size == 2 -> DECLARE_LAST is illegal
    state.hands[p] = [CANONICAL_CARD_BY_ID["CIRCLE_3"], CANONICAL_CARD_BY_ID["STAR_4"]]
    actions_2 = RulesEngine.legal_actions(state)
    assert not any(a.action_type == ActionType.DECLARE_LAST for a in actions_2)

    # 2. Hand size == 1, undeclared -> DECLARE_LAST is legal
    state.hands[p] = [CANONICAL_CARD_BY_ID["CIRCLE_3"]]
    state.last_card_declared[p] = False
    actions_1 = RulesEngine.legal_actions(state)
    assert any(a.action_type == ActionType.DECLARE_LAST for a in actions_1)

    # 3. Hand size == 1, already declared -> DECLARE_LAST is no longer legal
    state.last_card_declared[p] = True
    actions_declared = RulesEngine.legal_actions(state)
    assert not any(a.action_type == ActionType.DECLARE_LAST for a in actions_declared)


def test_action_mask_alignment():
    """Verify that action_mask produces exact 1-to-1 match with legal_actions."""
    state = GameState.create_initial_state(seed=42)
    legal = RulesEngine.legal_actions(state)
    mask = RulesEngine.action_mask(state)

    assert len(mask) == 76
    active_indices = [idx for idx, val in enumerate(mask) if val == 1]
    expected_indices = [a.action_id for a in legal]

    assert sorted(active_indices) == sorted(expected_indices)
