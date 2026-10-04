"""Unit tests for RandomLegalAgent and RuleBasedAgent baselines."""

import pytest
from tests.helpers import make_custom_state
from whot_ml.action import ActionType
from whot_ml.agents.random_agent import RandomLegalAgent
from whot_ml.agents.rule_based_agent import RuleBasedAgent
from whot_ml.card import CANONICAL_CARD_BY_ID, Shape, SpecialEffect
from whot_ml.observation import ObservationGenerator


def test_random_legal_agent_selects_legal_actions():
    """Verify RandomLegalAgent always selects an action from legal_actions."""
    state = make_custom_state(current_player=0)
    obs = ObservationGenerator.generate(state, player_id=0)

    agent = RandomLegalAgent(seed=42)
    agent.reset(player_id=0)

    for _ in range(20):
        action = agent.act(obs)
        assert action in obs.legal_actions


def test_rule_based_agent_declares_last_card():
    """Verify RuleBasedAgent prioritizes DECLARE_LAST when holding 1 card and undeclared."""
    state = make_custom_state(
        current_player=0,
        play_pile=[CANONICAL_CARD_BY_ID["CIRCLE_7"]],
        hands={0: [CANONICAL_CARD_BY_ID["CIRCLE_3"]]},
        last_card_declared={0: False},
    )
    obs = ObservationGenerator.generate(state, player_id=0)

    agent = RuleBasedAgent(seed=42)
    agent.reset(player_id=0)

    action = agent.act(obs)
    assert action.action_type == ActionType.DECLARE_LAST


def test_rule_based_agent_defends_penalty():
    """Verify RuleBasedAgent plays defending card when facing active penalty."""
    state = make_custom_state(
        current_player=0,
        active_penalty_type=SpecialEffect.PICK_TWO,
        active_penalty_count=2,
        play_pile=[CANONICAL_CARD_BY_ID["CIRCLE_2"]],
        hands={0: [CANONICAL_CARD_BY_ID["TRIANGLE_2"], CANONICAL_CARD_BY_ID["STAR_3"]]},
    )
    obs = ObservationGenerator.generate(state, player_id=0)

    agent = RuleBasedAgent(seed=42)
    agent.reset(player_id=0)

    action = agent.act(obs)
    assert action.action_type == ActionType.PLAY
    assert action.card_id == "TRIANGLE_2"


def test_rule_based_agent_whot_shape_selection_heuristic():
    """Verify RuleBasedAgent selects the shape it holds the most of when playing WHOT."""
    state = make_custom_state(
        current_player=0,
        play_pile=[CANONICAL_CARD_BY_ID["CROSS_10"]],
        hands={
            0: [
                CANONICAL_CARD_BY_ID["WHOT_1"],
                CANONICAL_CARD_BY_ID["STAR_3"],
                CANONICAL_CARD_BY_ID["STAR_7"],
                CANONICAL_CARD_BY_ID["CIRCLE_1"],
            ]
        },
    )
    obs = ObservationGenerator.generate(state, player_id=0)

    agent = RuleBasedAgent(seed=42)
    agent.reset(player_id=0)

    action = agent.act(obs)
    # Player holds 2 STAR cards, 1 CIRCLE card. Heuristic should call STAR!
    assert action.action_type == ActionType.PLAY_WHOT
    assert action.selected_shape == Shape.STAR
