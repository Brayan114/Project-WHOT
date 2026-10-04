"""WHOT-ML Research Simulator package."""

from whot_ml.version import BASELINE_ENVIRONMENT, SIMULATOR_VERSION
from whot_ml.card import (
    Card,
    Shape,
    CardType,
    SpecialEffect,
    create_standard_deck,
    CANONICAL_DECK,
    CANONICAL_CARD_BY_ID,
    CANONICAL_CARD_BY_INDEX,
    TOTAL_DECK_SIZE,
    NUM_ORDINARY_CARDS,
    NUM_WHOT_CARDS,
)
from whot_ml.ruleset import (
    WHOTConfig,
    TurnDirection,
    StarterPolicy,
    StackingMode,
    FinalCardOnePolicy,
    MarketExhaustionPolicy,
    InitialCardPolicy,
    LastCardViolationPenalty,
    get_baseline_config,
)
from whot_ml.action import (
    Action,
    ActionType,
    TOTAL_ACTIONS,
    ACTION_INDEX_DRAW,
    ACTION_INDEX_DECLARE_LAST,
    action_to_index,
    index_to_action,
    make_play_card_action,
    make_play_whot_action,
    make_draw_action,
    make_declare_last_action,
)
from whot_ml.rng_manager import RNGManager
from whot_ml.turn_manager import TurnManager, TurnModifier
from whot_ml.invariants import InvariantValidator, InvariantViolationError
from whot_ml.state import GameState
from whot_ml.rules_engine import RulesEngine, IllegalActionError
from whot_ml.event import Event, EventType
from whot_ml.effect_resolver import EffectResolver, StepResult
from whot_ml.observation import PlayerObservation, ObservationGenerator
from whot_ml.serializer import (
    serialize_state,
    restore_state,
    serialize_to_json,
    restore_from_json,
)
from whot_ml.metrics import (
    EpisodeMetrics,
    MetricsCollector,
    BatchMetrics,
    aggregate_metrics,
)
from whot_ml.environment import GameEnvironment, EnvStepResult
from whot_ml.agents import Agent, RandomLegalAgent, RuleBasedAgent
from whot_ml.runner import play_game, run_batch_evaluation

__all__ = [
    "BASELINE_ENVIRONMENT",
    "SIMULATOR_VERSION",
    "Card",
    "Shape",
    "CardType",
    "SpecialEffect",
    "create_standard_deck",
    "CANONICAL_DECK",
    "CANONICAL_CARD_BY_ID",
    "CANONICAL_CARD_BY_INDEX",
    "TOTAL_DECK_SIZE",
    "NUM_ORDINARY_CARDS",
    "NUM_WHOT_CARDS",
    "WHOTConfig",
    "TurnDirection",
    "StarterPolicy",
    "StackingMode",
    "FinalCardOnePolicy",
    "MarketExhaustionPolicy",
    "InitialCardPolicy",
    "LastCardViolationPenalty",
    "get_baseline_config",
    "Action",
    "ActionType",
    "TOTAL_ACTIONS",
    "ACTION_INDEX_DRAW",
    "ACTION_INDEX_DECLARE_LAST",
    "action_to_index",
    "index_to_action",
    "make_play_card_action",
    "make_play_whot_action",
    "make_draw_action",
    "make_declare_last_action",
    "RNGManager",
    "TurnManager",
    "TurnModifier",
    "InvariantValidator",
    "InvariantViolationError",
    "GameState",
    "RulesEngine",
    "IllegalActionError",
    "Event",
    "EventType",
    "EffectResolver",
    "StepResult",
    "PlayerObservation",
    "ObservationGenerator",
    "serialize_state",
    "restore_state",
    "serialize_to_json",
    "restore_from_json",
    "EpisodeMetrics",
    "MetricsCollector",
    "BatchMetrics",
    "aggregate_metrics",
    "GameEnvironment",
    "EnvStepResult",
    "Agent",
    "RandomLegalAgent",
    "RuleBasedAgent",
    "play_game",
    "run_batch_evaluation",
]
