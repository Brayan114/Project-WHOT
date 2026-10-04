"""Unit tests for Card Effects: Hold On, Pick Two, Pick Three, Suspension, General Market, WHOT."""

import pytest
from tests.helpers import make_custom_state
from whot_ml.action import (
    make_draw_action,
    make_play_card_action,
    make_play_whot_action,
)
from whot_ml.card import CANONICAL_CARD_BY_ID, Shape, SpecialEffect
from whot_ml.effect_resolver import EffectResolver
from whot_ml.event import EventType


def test_hold_on_card_one():
    """Verify Hold On (Card 1) grants the same player another turn."""
    card_1 = CANONICAL_CARD_BY_ID["CIRCLE_1"]
    other_card = CANONICAL_CARD_BY_ID["STAR_3"]

    state = make_custom_state(
        current_player=0,
        play_pile=[CANONICAL_CARD_BY_ID["CIRCLE_4"]],
        hands={0: [card_1, other_card]},
    )

    res = EffectResolver.apply_action(state, make_play_card_action(card_1))

    assert res.next_player == 0
    assert state.current_player == 0
    assert any(e.event_type == EventType.HOLD_ON_ACTIVATED for e in res.events)


def test_pick_two_stacking_and_forced_draw():
    """Verify Pick Two stacks (2 -> 4 -> 6) and accumulated penalty is drawn."""
    c2_0 = CANONICAL_CARD_BY_ID["CIRCLE_2"]
    c2_1 = CANONICAL_CARD_BY_ID["TRIANGLE_2"]
    c2_2 = CANONICAL_CARD_BY_ID["CROSS_2"]

    state = make_custom_state(
        current_player=0,
        play_pile=[CANONICAL_CARD_BY_ID["CIRCLE_4"]],
        hands={
            0: [c2_0, CANONICAL_CARD_BY_ID["STAR_3"]],
            1: [c2_1, CANONICAL_CARD_BY_ID["STAR_4"]],
            2: [c2_2, CANONICAL_CARD_BY_ID["STAR_5"]],
            3: [CANONICAL_CARD_BY_ID["STAR_7"]],  # Player 3 has no 2
        },
    )

    # Player 0 plays Circle 2
    res0 = EffectResolver.apply_action(state, make_play_card_action(c2_0))
    assert state.active_penalty_count == 2
    assert state.active_penalty_type == SpecialEffect.PICK_TWO
    assert res0.next_player == 1
    assert any(e.event_type == EventType.PENALTY_ACTIVATED for e in res0.events)

    # Player 1 stacks Triangle 2
    res1 = EffectResolver.apply_action(state, make_play_card_action(c2_1))
    assert state.active_penalty_count == 4
    assert res1.next_player == 2
    assert any(e.event_type == EventType.PENALTY_STACKED for e in res1.events)

    # Player 2 stacks Cross 2
    res2 = EffectResolver.apply_action(state, make_play_card_action(c2_2))
    assert state.active_penalty_count == 6
    assert res2.next_player == 3

    # Player 3 has no 2, must DRAW the accumulated penalty of 6 cards
    initial_hand_size = len(state.hands[3])
    res3 = EffectResolver.apply_action(state, make_draw_action())

    assert len(state.hands[3]) == initial_hand_size + 6
    assert state.active_penalty_count == 0
    assert state.active_penalty_type is None
    assert any(e.event_type == EventType.PENALTY_RESOLVED for e in res3.events)
    assert res3.next_player == 0


def test_pick_three_stacking_and_forced_draw():
    """Verify Pick Three stacks (3 -> 6) and accumulated penalty is drawn."""
    c5_0 = CANONICAL_CARD_BY_ID["CIRCLE_5"]
    c5_1 = CANONICAL_CARD_BY_ID["STAR_5"]

    state = make_custom_state(
        current_player=0,
        play_pile=[CANONICAL_CARD_BY_ID["CIRCLE_4"]],
        hands={
            0: [c5_0, CANONICAL_CARD_BY_ID["STAR_3"]],
            1: [c5_1, CANONICAL_CARD_BY_ID["STAR_4"]],
            2: [CANONICAL_CARD_BY_ID["STAR_7"]],
        },
    )

    EffectResolver.apply_action(state, make_play_card_action(c5_0))
    assert state.active_penalty_count == 3

    EffectResolver.apply_action(state, make_play_card_action(c5_1))
    assert state.active_penalty_count == 6

    # Player 2 draws 6
    initial_len = len(state.hands[2])
    EffectResolver.apply_action(state, make_draw_action())
    assert len(state.hands[2]) == initial_len + 6
    assert state.active_penalty_count == 0


def test_suspension_card_eight():
    """Verify Suspension (Card 8) skips next player in order."""
    card_8 = CANONICAL_CARD_BY_ID["CIRCLE_8"]
    state = make_custom_state(
        current_player=0,
        play_pile=[CANONICAL_CARD_BY_ID["CIRCLE_4"]],
        hands={0: [card_8, CANONICAL_CARD_BY_ID["STAR_3"]]},
    )

    res = EffectResolver.apply_action(state, make_play_card_action(card_8))

    assert res.next_player == 2  # Player 1 skipped, Player 2 is next
    assert state.current_player == 2
    assert any(e.event_type == EventType.TURN_SKIPPED for e in res.events)


def test_general_market_card_fourteen():
    """Verify General Market (Card 14) causes every other player to draw one card."""
    card_14 = CANONICAL_CARD_BY_ID["CIRCLE_14"]
    state = make_custom_state(
        current_player=0,
        play_pile=[CANONICAL_CARD_BY_ID["CIRCLE_4"]],
        hands={
            0: [card_14, CANONICAL_CARD_BY_ID["STAR_3"]],
            1: [CANONICAL_CARD_BY_ID["STAR_4"]],
            2: [CANONICAL_CARD_BY_ID["STAR_5"]],
            3: [CANONICAL_CARD_BY_ID["STAR_7"]],
        },
    )

    hand_sizes_before = {p: len(state.hands[p]) for p in range(4)}

    res = EffectResolver.apply_action(state, make_play_card_action(card_14))

    # Player 0 played 1 card, did not draw
    assert len(state.hands[0]) == hand_sizes_before[0] - 1
    # Players 1, 2, 3 each drew exactly 1 card
    for p in (1, 2, 3):
        assert len(state.hands[p]) == hand_sizes_before[p] + 1

    assert any(e.event_type == EventType.GENERAL_MARKET_ACTIVATED for e in res.events)
    assert res.next_player == 1


def test_whot_shape_selection():
    """Verify WHOT sets the active call to selected shape."""
    whot_card = CANONICAL_CARD_BY_ID["WHOT_1"]
    state = make_custom_state(
        current_player=0,
        play_pile=[CANONICAL_CARD_BY_ID["CIRCLE_4"]],
        hands={0: [whot_card, CANONICAL_CARD_BY_ID["STAR_3"]]},
    )

    res = EffectResolver.apply_action(
        state, make_play_whot_action(whot_card, Shape.STAR)
    )

    assert state.current_call == Shape.STAR
    assert state.top_card == whot_card
    assert any(e.event_type == EventType.WHOT_SHAPE_SELECTED for e in res.events)
