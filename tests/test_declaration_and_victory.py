"""Unit tests for Pre-flight Check 2: Declaration state machine, undeclared penalties, and terminal victory."""

import pytest
from tests.helpers import make_custom_state
from whot_ml.action import (
    make_declare_last_action,
    make_play_card_action,
    make_play_whot_action,
)
from whot_ml.card import CANONICAL_CARD_BY_ID, Shape
from whot_ml.effect_resolver import EffectResolver
from whot_ml.event import EventType
from whot_ml.rules_engine import IllegalActionError


def test_declared_final_card_produces_valid_victory():
    """Verify:
    1. Player with 1 card declares last card (turn does not advance).
    2. Player plays final matching card.
    3. Game terminates, winner receives +1, losers receive -1.
    """
    final_card = CANONICAL_CARD_BY_ID["CIRCLE_3"]
    state = make_custom_state(
        current_player=0,
        play_pile=[CANONICAL_CARD_BY_ID["CIRCLE_7"]],
        hands={0: [final_card]},
        last_card_declared={0: False, 1: False, 2: False, 3: False},
    )

    # Step 1: Player explicitly declares last card
    res_dec = EffectResolver.apply_action(state, make_declare_last_action())

    assert state.last_card_declared[0] is True
    assert res_dec.next_player == 0  # Baseline: declaration does not consume the turn!
    assert state.current_player == 0
    assert not res_dec.terminated
    assert any(e.event_type == EventType.LAST_CARD_DECLARED for e in res_dec.events)

    # Step 2: Player plays final card
    res_play = EffectResolver.apply_action(state, make_play_card_action(final_card))

    assert res_play.terminated is True
    assert state.is_terminal is True
    assert state.winner == 0
    assert res_play.rewards[0] == 1.0
    for opponent in (1, 2, 3):
        assert res_play.rewards[opponent] == -1.0

    assert any(e.event_type == EventType.ROUND_ENDED for e in res_play.events)
    assert any(e.event_type == EventType.GAME_OVER for e in res_play.events)


def test_undeclared_final_card_incurs_penalty_and_game_continues():
    """Verify:
    1. Player with 1 card does NOT declare.
    2. Player attempts to play final card to win.
    3. Simulator detects undeclared victory attempt.
    4. LAST_CARD_DECLARATION_VIOLATION event emitted.
    5. Player draws 1 penalty card. Hand size becomes 1.
    6. Game does NOT terminate and turn advances.
    """
    final_card = CANONICAL_CARD_BY_ID["CIRCLE_3"]
    state = make_custom_state(
        current_player=0,
        play_pile=[CANONICAL_CARD_BY_ID["CIRCLE_7"]],
        hands={0: [final_card]},
        last_card_declared={0: False, 1: False, 2: False, 3: False},
    )

    res = EffectResolver.apply_action(state, make_play_card_action(final_card))

    # Must NOT be terminal
    assert res.terminated is False
    assert state.is_terminal is False
    assert state.winner is None

    # Penalty applied: 1 card drawn into hand
    assert len(state.hands[0]) == 1
    assert any(e.event_type == EventType.LAST_CARD_DECLARATION_VIOLATION for e in res.events)

    # Turn advances to next player
    assert res.next_player != 0


def test_final_card_one_rejected_by_rules_engine():
    """Verify Card 1 (Hold On) cannot produce a victory."""
    card_1 = CANONICAL_CARD_BY_ID["CIRCLE_1"]
    state = make_custom_state(
        current_player=0,
        play_pile=[CANONICAL_CARD_BY_ID["CIRCLE_7"]],
        hands={0: [card_1]},
        last_card_declared={0: True},
    )

    with pytest.raises(IllegalActionError):
        EffectResolver.apply_action(state, make_play_card_action(card_1))


def test_other_special_cards_can_be_winning_final_cards():
    """Verify 2, 5, 8, 14, and WHOT can win as declared final cards."""
    # Test Card 14 (General Market) as winning card
    card_14 = CANONICAL_CARD_BY_ID["CIRCLE_14"]
    state = make_custom_state(
        current_player=0,
        play_pile=[CANONICAL_CARD_BY_ID["CIRCLE_7"]],
        hands={0: [card_14]},
        last_card_declared={0: True},
    )

    res = EffectResolver.apply_action(state, make_play_card_action(card_14))

    assert any(e.event_type == EventType.GENERAL_MARKET_ACTIVATED for e in res.events)
    assert res.terminated is True
    assert state.winner == 0

    # Test WHOT as winning card
    whot_card = CANONICAL_CARD_BY_ID["WHOT_1"]
    state_whot = make_custom_state(
        current_player=1,
        play_pile=[CANONICAL_CARD_BY_ID["CIRCLE_7"]],
        hands={1: [whot_card]},
        last_card_declared={1: True},
    )

    res_whot = EffectResolver.apply_action(
        state_whot, make_play_whot_action(whot_card, Shape.TRIANGLE)
    )
    assert res_whot.terminated is True
    assert state_whot.winner == 1
