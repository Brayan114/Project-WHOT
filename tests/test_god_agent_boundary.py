"""Unit test verifying the architectural boundary between God-Agent and Standard Agent."""

import pytest
from tests.helpers import make_custom_state
from whot_ml.card import CANONICAL_CARD_BY_ID
from whot_ml.observation import ObservationGenerator, PlayerObservation
from whot_ml.state import GameState


class GodAgent:
    """Validation-only Oracle / Cheating Agent that operates on full GameState."""

    def peek_opponent_hand(self, state: GameState, opponent_id: int):
        return [c.id for c in state.hands[opponent_id]]

    def peek_next_draw(self, state: GameState):
        return state.market[-1].id if state.market else None


class StandardAgent:
    """Normal agent that receives only PlayerObservation."""

    def get_own_hand(self, obs: PlayerObservation):
        return [c.id for c in obs.hand]


def test_god_agent_vs_standard_agent_boundary():
    """Verify GodAgent has full-state access, while StandardAgent cannot access hidden data."""
    secret_card = CANONICAL_CARD_BY_ID["STAR_8"]
    state = make_custom_state(
        current_player=0,
        hands={
            0: [CANONICAL_CARD_BY_ID["CIRCLE_1"]],
            1: [secret_card],
        },
    )

    god_agent = GodAgent()
    std_agent = StandardAgent()

    # 1. God Agent can see opponent 1's secret card from GameState
    opp_hand = god_agent.peek_opponent_hand(state, opponent_id=1)
    assert secret_card.id in opp_hand

    # 2. Standard Agent receives only PlayerObservation
    obs = ObservationGenerator.generate(state, player_id=0)
    own_hand = std_agent.get_own_hand(obs)
    assert own_hand == ["CIRCLE_1"]

    # 3. Standard Agent CANNOT access forbidden hidden fields on PlayerObservation
    with pytest.raises(AttributeError):
        _ = obs.market  # type: ignore

    with pytest.raises(AttributeError):
        _ = obs.hands  # type: ignore

    with pytest.raises(AttributeError):
        _ = obs.rng_manager  # type: ignore
