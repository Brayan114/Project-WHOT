"""Regression tests verifying the exact Victory Pipeline evaluation order (P0-D4 Section 26, 27).

Order:
  PLAY FINAL CARD
  -> CHECK DECLARATION REQUIREMENT
  -> if declared: VALID VICTORY
  -> if undeclared: APPLY CONFIGURED PENALTY + CONTINUE

The game must never temporarily enter a terminal state before the declaration check.
"""

import pytest
from tests.helpers import make_custom_state
from whot_ml.action import make_play_card_action
from whot_ml.card import CANONICAL_CARD_BY_ID, Shape
from whot_ml.effect_resolver import EffectResolver
from whot_ml.event import EventType


def test_victory_pipeline_evaluation_order_undeclared():
    """Verify that undeclared final play does NOT temporarily flag terminal or award win."""
    final_card = CANONICAL_CARD_BY_ID["CIRCLE_3"]
    state = make_custom_state(
        current_player=0,
        play_pile=[CANONICAL_CARD_BY_ID["CIRCLE_7"]],
        hands={0: [final_card]},
        last_card_declared={0: False},
    )

    assert state.is_terminal is False
    assert state.winner is None

    res = EffectResolver.apply_action(state, make_play_card_action(final_card))

    # Invariants:
    # 1. Terminal must be False throughout and after
    assert res.terminated is False
    assert state.is_terminal is False
    assert state.winner is None

    # 2. Rewards must remain zero (no victory points awarded)
    assert res.rewards[0] == 0.0
    for p in range(4):
        assert res.rewards[p] == 0.0

    # 3. Events must record VIOLATION and NOT ROUND_ENDED / GAME_OVER
    event_types = [e.event_type for e in res.events]
    assert EventType.LAST_CARD_DECLARATION_VIOLATION in event_types
    assert EventType.ROUND_ENDED not in event_types
    assert EventType.GAME_OVER not in event_types

    # 4. Player drew 1 penalty card, hand size is now 1
    assert len(state.hands[0]) == 1

    # 5. Game continues to next player
    assert res.next_player == 1
    assert state.current_player == 1
