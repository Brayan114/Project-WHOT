"""Unit tests for Public vs Private event stream separation (P0-D4 Section 35)."""

import pytest
from tests.helpers import make_custom_state
from whot_ml.action import make_draw_action
from whot_ml.card import CANONICAL_CARD_BY_ID
from whot_ml.effect_resolver import EffectResolver
from whot_ml.event import Event, EventType
from whot_ml.observation import ObservationGenerator


def test_public_and_private_event_separation_on_draw():
    """Verify that when a player draws:
    1. A public CARD_DRAWN event is emitted without card_id.
    2. A private PRIVATE_CARD_RECEIVED event is emitted with card_id for recipient.
    3. Other players' observations receive only public events, never opponent's private events.
    """
    state = make_custom_state(
        current_player=1,
        play_pile=[CANONICAL_CARD_BY_ID["CIRCLE_4"]],
        hands={1: [CANONICAL_CARD_BY_ID["STAR_8"]]},  # Genuinely unplayable on Circle 4
    )

    # Player 1 draws
    res = EffectResolver.apply_action(state, make_draw_action())

    # Find the draw events in the step result
    public_draw_events = [e for e in res.events if e.event_type == EventType.CARD_DRAWN]
    private_draw_events = [e for e in res.events if e.event_type == EventType.PRIVATE_CARD_RECEIVED]

    assert len(public_draw_events) == 1
    assert public_draw_events[0].is_public is True
    assert public_draw_events[0].card_id is None  # Public MUST NOT leak card identity!
    assert public_draw_events[0].player == 1

    assert len(private_draw_events) == 1
    assert private_draw_events[0].is_public is False
    assert private_draw_events[0].card_id is not None  # Private card identity present
    assert private_draw_events[0].player == 1

    # Observation for Player 0 (opponent):
    obs_0 = ObservationGenerator.generate(state, player_id=0, history=res.events)
    # Opponent sees public history
    assert any(e.event_type == EventType.CARD_DRAWN for e in obs_0.public_history)
    # Opponent does NOT receive Player 1's private event
    assert len(obs_0.private_events) == 0

    # Observation for Player 1 (recipient):
    obs_1 = ObservationGenerator.generate(state, player_id=1, history=res.events)
    assert any(e.event_type == EventType.CARD_DRAWN for e in obs_1.public_history)
    assert any(e.event_type == EventType.PRIVATE_CARD_RECEIVED for e in obs_1.private_events)
