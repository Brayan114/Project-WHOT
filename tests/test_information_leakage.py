"""Critical Information-Leakage tests (P0-D2, P0-D4 Section 42.4, 43).

Verifies the strict separation between GameState (Full World State) and PlayerObservation.
Protects subsequent ML research (Papers 1-4) from hidden-information contamination.
"""

import json
import pytest
from tests.helpers import make_custom_state
from whot_ml.action import make_draw_action, make_play_card_action
from whot_ml.card import CANONICAL_CARD_BY_ID, Shape
from whot_ml.effect_resolver import EffectResolver
from whot_ml.observation import ObservationGenerator, PlayerObservation
from whot_ml.serializer import restore_state, serialize_state


def test_leakage_1_different_opponent_hands_yield_identical_observation():
    """Requirement 1:
    Two states A and B with identical public information and identical player 0 hand,
    but with different opponent hidden hands, MUST produce identical observations for player 0.
    """
    card_own1 = CANONICAL_CARD_BY_ID["CIRCLE_3"]
    card_own2 = CANONICAL_CARD_BY_ID["STAR_4"]

    # State A: Player 1 has Triangle 10, Player 2 has Square 11
    state_a = make_custom_state(
        current_player=0,
        play_pile=[CANONICAL_CARD_BY_ID["CIRCLE_7"]],
        hands={
            0: [card_own1, card_own2],
            1: [CANONICAL_CARD_BY_ID["TRIANGLE_10"], CANONICAL_CARD_BY_ID["CROSS_1"]],
            2: [CANONICAL_CARD_BY_ID["SQUARE_11"], CANONICAL_CARD_BY_ID["STAR_8"]],
            3: [CANONICAL_CARD_BY_ID["STAR_1"]],
        },
    )

    # State B: Swap hidden cards between Player 1 and Player 2
    state_b = make_custom_state(
        current_player=0,
        play_pile=[CANONICAL_CARD_BY_ID["CIRCLE_7"]],
        hands={
            0: [card_own1, card_own2],  # Identical own hand
            1: [CANONICAL_CARD_BY_ID["SQUARE_11"], CANONICAL_CARD_BY_ID["STAR_8"]],  # Swapped
            2: [CANONICAL_CARD_BY_ID["TRIANGLE_10"], CANONICAL_CARD_BY_ID["CROSS_1"]],  # Swapped
            3: [CANONICAL_CARD_BY_ID["STAR_1"]],  # Same size (1 card)
        },
    )

    obs_a = ObservationGenerator.generate(state_a, player_id=0)
    obs_b = ObservationGenerator.generate(state_b, player_id=0)

    # Strictly equal value!
    assert obs_a == obs_b
    assert obs_a.to_dict() == obs_b.to_dict()


def test_leakage_2_market_order_change_yields_identical_observation():
    """Requirement 2:
    Changing the hidden order of cards in the market draw pile MUST NOT change the player's observation.
    """
    state_a = make_custom_state(current_player=0)
    state_b = make_custom_state(current_player=0)

    # Reverse the hidden market order in state_b
    state_b.market = list(reversed(state_a.market))

    obs_a = ObservationGenerator.generate(state_a, player_id=0)
    obs_b = ObservationGenerator.generate(state_b, player_id=0)

    assert obs_a == obs_b
    assert obs_a.to_dict() == obs_b.to_dict()


def test_leakage_3_rng_state_never_present_in_observation():
    """Requirement 3:
    Simulator RNG state or future random outcomes must NEVER be present in PlayerObservation.
    """
    state = make_custom_state(current_player=0, seed=12345)
    obs = ObservationGenerator.generate(state, player_id=0)

    # Neither object attributes nor serialized dictionary may contain RNG references
    assert not hasattr(obs, "rng_state")
    assert not hasattr(obs, "rng_manager")
    obs_dict = obs.to_dict()
    assert "rng_state" not in obs_dict
    assert "rng_manager" not in obs_dict

    # Changing RNG state in simulator leaves observation identical
    _ = [state.rng_manager.randint(0, 100) for _ in range(50)]
    obs_after = ObservationGenerator.generate(state, player_id=0)
    assert obs == obs_after


def test_leakage_4_opponent_card_identities_cannot_be_recovered_from_serialized_observation():
    """Requirement 4:
    A JSON-serialized PlayerObservation dictionary must contain zero mentions of opponent card IDs.
    """
    opp_secret_card = CANONICAL_CARD_BY_ID["STAR_7"]
    state = make_custom_state(
        current_player=0,
        hands={
            0: [CANONICAL_CARD_BY_ID["CIRCLE_1"]],
            1: [opp_secret_card],  # Opponent holds STAR_7
        },
    )

    obs = ObservationGenerator.generate(state, player_id=0)
    serialized_json = json.dumps(obs.to_dict())

    # Opponent's card ID "STAR_7" must NOT appear anywhere in the serialized observation string!
    assert "STAR_7" not in serialized_json
    # Player 0's own card ID "CIRCLE_1" SHOULD appear
    assert "CIRCLE_1" in serialized_json


def test_leakage_5_state_serialization_round_trip_is_lossless():
    """Requirement 5:
    Full GameState serialization to dict and restoration preserves all state fields bitwise.
    """
    state = make_custom_state(
        current_player=1,
        active_penalty_type=CANONICAL_CARD_BY_ID["CIRCLE_2"].default_effect,
        active_penalty_count=4,
        hands={
            0: [CANONICAL_CARD_BY_ID["CIRCLE_1"]],
            1: [CANONICAL_CARD_BY_ID["CIRCLE_2"]],
        },
    )

    serialized = serialize_state(state)
    restored = restore_state(serialized)

    assert restored.current_player == state.current_player
    assert restored.current_call == state.current_call
    assert restored.active_penalty_type == state.active_penalty_type
    assert restored.active_penalty_count == state.active_penalty_count
    assert [c.id for c in restored.play_pile] == [c.id for c in state.play_pile]
    assert [c.id for c in restored.market] == [c.id for c in state.market]
    for p in range(state.config.player_count):
        assert [c.id for c in restored.hands[p]] == [c.id for c in state.hands[p]]


def test_leakage_6_restoration_and_continuation_is_deterministic():
    """Requirement 6:
    Restoring a serialized state and continuing with an action sequence produces
    the exact same future game state as continuing from the original state.
    """
    state_original = make_custom_state(
        current_player=0,
        play_pile=[CANONICAL_CARD_BY_ID["CIRCLE_4"]],
        hands={
            0: [CANONICAL_CARD_BY_ID["CIRCLE_1"], CANONICAL_CARD_BY_ID["STAR_3"]],
            1: [CANONICAL_CARD_BY_ID["STAR_5"]],
        },
    )

    # Serialize at checkpoint
    serialized = serialize_state(state_original)
    state_restored = restore_state(serialized)

    # Action 1: Player 0 plays Circle 1 (Hold On)
    res_orig_1 = EffectResolver.apply_action(
        state_original, make_play_card_action(CANONICAL_CARD_BY_ID["CIRCLE_1"])
    )
    res_rest_1 = EffectResolver.apply_action(
        state_restored, make_play_card_action(CANONICAL_CARD_BY_ID["CIRCLE_1"])
    )

    assert res_orig_1.next_player == res_rest_1.next_player
    assert [e.event_type for e in res_orig_1.events] == [e.event_type for e in res_rest_1.events]

    # Action 2: Player 0 draws a card
    res_orig_2 = EffectResolver.apply_action(state_original, make_draw_action())
    res_rest_2 = EffectResolver.apply_action(state_restored, make_draw_action())

    assert res_orig_2.next_player == res_rest_2.next_player
    assert [c.id for c in state_original.hands[0]] == [c.id for c in state_restored.hands[0]]
    assert [c.id for c in state_original.market] == [c.id for c in state_restored.market]
