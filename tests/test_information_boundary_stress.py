"""Systematic information boundary stress audit (P0-D2, P0-D4 Section 43)."""

import json
import pytest
from tests.helpers import make_custom_state
from whot_ml.action import make_draw_action
from whot_ml.card import CANONICAL_CARD_BY_ID
from whot_ml.environment import GameEnvironment
from whot_ml.rules_engine import IllegalActionError


def test_agent_observation_attributes_audit():
    """Verify that PlayerObservation has zero references to hidden state."""
    env = GameEnvironment()
    env.reset(seed=42)
    obs = env.observe(0)

    # Permitted attributes
    permitted_attrs = {
        "player_id",
        "hand",
        "play_pile",
        "current_call",
        "current_player",
        "active_penalty_type",
        "active_penalty_count",
        "hand_sizes",
        "last_card_declared",
        "market_size",
        "public_history",
        "private_events",
        "action_mask",
        "ruleset",
        "timestep",
        "turn_count",
        "is_terminal",
        "winner",
        "top_card",
        "is_my_turn",
        "legal_actions",
        "to_dict",
        "from_dict",
    }

    obs_attrs = {attr for attr in dir(obs) if not attr.startswith("_")}
    forbidden_exposed = obs_attrs - permitted_attrs
    assert not forbidden_exposed, f"Found forbidden attributes exposed on PlayerObservation: {forbidden_exposed}"


def test_step_info_payload_leakage_audit():
    """Verify that EnvStepResult.info contains zero hidden card references."""
    env = GameEnvironment()
    env.reset(seed=42)

    curr = env.current_player
    actions = env.legal_actions(curr)
    step_result = env.step(actions[0], acting_player=curr)

    info = step_result.info
    info_str = str(info)

    # Opponent hands must not appear in info
    for p in range(4):
        if p != curr:
            for card in env.state.hands[p]:
                # Secret card ID should not be in info_str unless it was legally played onto play_pile
                if card not in env.state.play_pile:
                    assert f"'{card.id}'" not in info_str and f'"{card.id}"' not in info_str, f"Secret card {card.id} leaked in step info!"


def test_serialized_observation_json_audit():
    """Scan the entire JSON-dumped PlayerObservation for any mention of opponents' cards or market cards."""
    env = GameEnvironment()
    env.reset(seed=123)

    for p in range(4):
        obs = env.observe(p)
        obs_json = json.dumps(obs.to_dict())

        # Collect all secret cards that player p must NOT know about
        secret_cards = []
        for opp in range(4):
            if opp != p:
                secret_cards.extend(env.state.hands[opp])
        secret_cards.extend(env.state.market)

        for secret_card in secret_cards:
            assert f'"{secret_card.id}"' not in obs_json, (
                f"Information leak detected: Secret card {secret_card.id} "
                f"found in Player {p}'s observation JSON!"
            )


def test_exception_messages_do_not_leak_hidden_state():
    """Verify that IllegalActionError messages contain no hidden opponent information."""
    env = GameEnvironment()
    env.reset(seed=42)

    curr = env.current_player
    non_curr = (curr + 1) % 4
    act = env.legal_actions(curr)[0]

    with pytest.raises(IllegalActionError) as exc_info:
        env.step(act, acting_player=non_curr)

    err_msg = str(exc_info.value)
    # Check that error message does not disclose opponent hand contents
    for card in env.state.hands[curr]:
        if card not in env.state.play_pile:
            assert card.id not in err_msg
