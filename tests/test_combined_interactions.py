"""Integration tests for combined card effect interactions in WHOT-ML (P0-D4)."""

import pytest
from tests.helpers import make_custom_state
from whot_ml.action import (
    make_declare_last_action,
    make_draw_action,
    make_play_card_action,
)
from whot_ml.card import CANONICAL_CARD_BY_ID, Shape, SpecialEffect
from whot_ml.effect_resolver import EffectResolver
from whot_ml.event import EventType


def test_hold_on_plus_declaration():
    """Interaction: Player plays Hold On (Card 1) down to 1 card.
    Because Card 1 gives another turn, player immediately holds the turn at hand_size == 1.
    Player then declares, and plays final card to win!
    """
    card_1 = CANONICAL_CARD_BY_ID["CIRCLE_1"]
    final_card = CANONICAL_CARD_BY_ID["CIRCLE_4"]

    state = make_custom_state(
        current_player=0,
        play_pile=[CANONICAL_CARD_BY_ID["CIRCLE_7"]],
        hands={0: [card_1, final_card]},
    )

    # Step 1: Play Card 1. Hand becomes 1. Hold On retains turn!
    res1 = EffectResolver.apply_action(state, make_play_card_action(card_1))
    assert res1.next_player == 0
    assert state.current_player == 0
    assert len(state.hands[0]) == 1

    # Step 2: Player declares last card
    res2 = EffectResolver.apply_action(state, make_declare_last_action())
    assert state.last_card_declared[0] is True
    assert res2.next_player == 0

    # Step 3: Player plays final card and wins
    res3 = EffectResolver.apply_action(state, make_play_card_action(final_card))
    assert res3.terminated is True
    assert state.winner == 0


def test_suspension_plus_penalty():
    """Interaction: Player 0 plays Suspension (8). Player 1 is skipped.
    Player 2 acts and plays Pick Two (2).
    Penalty must fall on Player 3 (not Player 1).
    """
    card_8 = CANONICAL_CARD_BY_ID["CIRCLE_8"]
    card_2 = CANONICAL_CARD_BY_ID["CIRCLE_2"]

    state = make_custom_state(
        current_player=0,
        play_pile=[CANONICAL_CARD_BY_ID["CIRCLE_7"]],
        hands={
            0: [card_8, CANONICAL_CARD_BY_ID["STAR_3"]],
            2: [card_2, CANONICAL_CARD_BY_ID["STAR_4"]],
        },
    )

    # Player 0 plays 8 -> Player 1 skipped -> Player 2 is next
    res0 = EffectResolver.apply_action(state, make_play_card_action(card_8))
    assert res0.next_player == 2
    assert state.current_player == 2

    # Player 2 plays Pick Two
    res2 = EffectResolver.apply_action(state, make_play_card_action(card_2))

    assert res2.next_player == 3  # Penalty falls on Player 3
    assert state.active_penalty_type == SpecialEffect.PICK_TWO
    assert state.active_penalty_count == 2


def test_general_market_near_empty_market():
    """Interaction: General Market played when market has fewer cards than opponents.
    Market exhausts midway through opponent draws, triggers reshuffle, and finishes draws.
    """
    card_14 = CANONICAL_CARD_BY_ID["CIRCLE_14"]
    c1 = CANONICAL_CARD_BY_ID["CIRCLE_1"]
    c2 = CANONICAL_CARD_BY_ID["CIRCLE_2"]
    c3 = CANONICAL_CARD_BY_ID["CIRCLE_3"]
    top = CANONICAL_CARD_BY_ID["CIRCLE_4"]

    state = make_custom_state(
        current_player=0,
        play_pile=[c1, c2, c3, top],
        hands={
            0: [card_14, CANONICAL_CARD_BY_ID["STAR_1"]],
            1: [CANONICAL_CARD_BY_ID["STAR_2"]],
            2: [CANONICAL_CARD_BY_ID["STAR_3"]],
            3: [CANONICAL_CARD_BY_ID["STAR_4"]],
        },
    )

    # Put all remaining market cards into hands except exactly 1 card
    while len(state.market) > 1:
        extra = state.market.pop()
        state.hands[1].append(extra)

    assert len(state.market) == 1
    assert len(state.play_pile) == 4

    hand_sizes_before = {p: len(state.hands[p]) for p in range(4)}

    # Player 0 plays 14 -> 3 opponents need to draw, but market has only 1 card!
    res = EffectResolver.apply_action(state, make_play_card_action(card_14))

    # All 3 opponents drew 1 card
    for p in (1, 2, 3):
        assert len(state.hands[p]) == hand_sizes_before[p] + 1

    # Market was reshuffled during the process
    assert any(e.event_type == EventType.MARKET_RESHUFFLED for e in res.events)

    # Top card Circle 14 preserved in play pile
    assert state.top_card == card_14


def test_stacking_plus_market_exhaustion():
    """Interaction: Pick Two stacked to 6 cards when market has only 2 cards.
    Player draws penalty -> market exhausts -> discards reshuffle -> all 6 cards drawn.
    """
    c_top = CANONICAL_CARD_BY_ID["CIRCLE_2"]
    c1 = CANONICAL_CARD_BY_ID["CIRCLE_1"]
    c3 = CANONICAL_CARD_BY_ID["CIRCLE_3"]
    c4 = CANONICAL_CARD_BY_ID["CIRCLE_4"]
    c7 = CANONICAL_CARD_BY_ID["CIRCLE_7"]

    state = make_custom_state(
        current_player=3,
        play_pile=[c1, c3, c4, c7, c_top],
        active_penalty_type=SpecialEffect.PICK_TWO,
        active_penalty_count=6,
        hands={3: [CANONICAL_CARD_BY_ID["STAR_1"]]},
    )

    # Leave only 2 cards in market
    while len(state.market) > 2:
        extra = state.market.pop()
        state.hands[0].append(extra)

    assert len(state.market) == 2
    initial_hand_len = len(state.hands[3])

    # Player 3 draws the 6-card penalty
    res = EffectResolver.apply_action(state, make_draw_action())

    assert len(state.hands[3]) == initial_hand_len + 6
    assert state.active_penalty_count == 0
    assert any(e.event_type == EventType.MARKET_RESHUFFLED for e in res.events)
