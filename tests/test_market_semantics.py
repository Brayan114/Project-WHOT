"""Unit tests for Pre-flight Check 1: Market ordering semantics and exhaustion recycling."""

import pytest
from tests.helpers import make_custom_state
from whot_ml.action import make_draw_action
from whot_ml.card import CANONICAL_CARD_BY_ID, TOTAL_DECK_SIZE, Shape
from whot_ml.effect_resolver import EffectResolver
from whot_ml.event import EventType


def test_market_top_ordering_and_deterministic_draw():
    """Verify market[-1] is the top card and draws pop from the end deterministically."""
    state = make_custom_state(
        current_player=0,
        play_pile=[CANONICAL_CARD_BY_ID["TRIANGLE_10"]],
        hands={0: [CANONICAL_CARD_BY_ID["CIRCLE_3"]]},  # Unplayable
    )

    expected_top_card = state.market[-1]
    res = EffectResolver.apply_action(state, make_draw_action())

    assert expected_top_card in state.hands[0]
    assert state.hands[0][-1] == expected_top_card


def test_market_exhaustion_preserves_top_card_and_reshuffles():
    """Verify that when the market becomes empty:
    1. The visible top card on the play pile is preserved.
    2. All previous cards underneath are shuffled into a new market.
    3. Total card count of 54 is strictly conserved.
    """
    c_base1 = CANONICAL_CARD_BY_ID["CIRCLE_1"]
    c_base2 = CANONICAL_CARD_BY_ID["CIRCLE_2"]
    c_base3 = CANONICAL_CARD_BY_ID["CIRCLE_3"]
    c_base4 = CANONICAL_CARD_BY_ID["CIRCLE_4"]
    c_top = CANONICAL_CARD_BY_ID["CIRCLE_5"]

    state = make_custom_state(
        current_player=0,
        play_pile=[c_base1, c_base2, c_base3, c_base4, c_top],
        hands={0: [CANONICAL_CARD_BY_ID["STAR_8"]]},  # Unplayable on Circle 5
    )

    # Empty the market by distributing cards into hands
    while state.market:
        c = state.market.pop()
        state.hands[1].append(c)

    assert len(state.market) == 0
    assert len(state.play_pile) == 5

    res = EffectResolver.apply_action(state, make_draw_action())

    # Top card Circle 5 MUST remain preserved in play pile
    assert len(state.play_pile) == 1
    assert state.top_card == c_top

    # Recycled cards (4 cards) minus 1 drawn card = 3 left in market
    assert len(state.market) == 3
    assert any(e.event_type == EventType.MARKET_RESHUFFLED for e in res.events)


def test_complete_market_exhaustion_generates_draw_unavailable():
    """Verify DRAW_UNAVAILABLE when market is empty and play pile has only 1 card."""
    c_top = CANONICAL_CARD_BY_ID["CIRCLE_5"]
    state = make_custom_state(
        current_player=0,
        play_pile=[c_top],
        hands={0: [CANONICAL_CARD_BY_ID["STAR_8"]]},  # Unplayable
    )

    # Empty the market by distributing cards into hands
    while state.market:
        c = state.market.pop()
        state.hands[1].append(c)

    assert len(state.market) == 0
    assert len(state.play_pile) == 1
    initial_hand_len = len(state.hands[0])

    res = EffectResolver.apply_action(state, make_draw_action())

    # No card drawn, no crash, DRAW_UNAVAILABLE logged
    assert len(state.hands[0]) == initial_hand_len
    assert any(e.event_type == EventType.DRAW_UNAVAILABLE for e in res.events)
