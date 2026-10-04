"""High-level GameEnvironment for WHOT-ML (P0-D4 Section 33)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from whot_ml.action import Action
from whot_ml.event import Event, EventType
from whot_ml.effect_resolver import EffectResolver, StepResult
from whot_ml.metrics import EpisodeMetrics, MetricsCollector
from whot_ml.observation import ObservationGenerator, PlayerObservation
from whot_ml.rules_engine import IllegalActionError, RulesEngine
from whot_ml.ruleset import WHOTConfig, get_baseline_config
from whot_ml.serializer import restore_state, serialize_state
from whot_ml.state import GameState


@dataclass(frozen=True)
class EnvStepResult:
    """Standard transition result returned by GameEnvironment.step()."""
    observation: PlayerObservation
    rewards: Dict[int, float]
    terminated: bool
    truncated: bool
    info: Dict[str, Any]
    acting_player: int
    next_player: int


class GameEnvironment:
    """The unified, research-facing multi-agent WHOT environment.

    Orchestrates GameState, RulesEngine, EffectResolver, ObservationGenerator,
    and MetricsCollector while strictly enforcing information boundaries.
    """

    def __init__(self, config: Optional[WHOTConfig] = None) -> None:
        self.config: WHOTConfig = config if config is not None else get_baseline_config()
        self.state: Optional[GameState] = None
        self.history: List[Event] = []
        self.metrics_collector: MetricsCollector = MetricsCollector()

    @property
    def current_player(self) -> int:
        """The index of the player whose turn it currently is to act."""
        if self.state is None:
            raise RuntimeError("Environment not initialized; call reset() first")
        return self.state.current_player

    @property
    def is_terminal(self) -> bool:
        if self.state is None:
            return False
        return self.state.is_terminal

    @property
    def winner(self) -> Optional[int]:
        if self.state is None:
            return None
        return self.state.winner

    def reset(
        self,
        seed: Optional[int] = None,
        ruleset: Optional[WHOTConfig] = None,
    ) -> Dict[int, PlayerObservation]:
        """Reset the environment, deal starting hands, and return initial observations for all players."""
        if ruleset is not None:
            self.config = ruleset

        self.state = GameState.create_initial_state(config=self.config, seed=seed)
        self.history = [
            Event(
                event_type=EventType.GAME_STARTED,
                timestep=0,
                player=self.state.current_player,
                details={"seed": seed, "ruleset": self.config.ruleset_name},
            )
        ]
        self.metrics_collector = MetricsCollector(episode_id=self.state.episode_id)

        # Return observation for each player
        return {p: self.observe(p) for p in range(self.config.player_count)}

    def observe(self, player_id: int) -> PlayerObservation:
        """Return the strictly isolated PlayerObservation for the given player."""
        if self.state is None:
            raise RuntimeError("Environment not initialized; call reset() first")
        return ObservationGenerator.generate(self.state, player_id, history=self.history)

    def legal_actions(self, player_id: Optional[int] = None) -> List[Action]:
        """Return all legal actions for a player (defaults to current player)."""
        if self.state is None:
            raise RuntimeError("Environment not initialized; call reset() first")
        target_player = player_id if player_id is not None else self.state.current_player
        return RulesEngine.legal_actions(self.state, target_player)

    def action_mask(self, player_id: Optional[int] = None) -> List[int]:
        """Return the 76-slot action mask for a player."""
        if self.state is None:
            raise RuntimeError("Environment not initialized; call reset() first")
        target_player = player_id if player_id is not None else self.state.current_player
        return RulesEngine.action_mask(self.state, target_player)

    def step(self, action: Action, acting_player: Optional[int] = None) -> EnvStepResult:
        """Execute an action for the active player.

        Enforces that only the current player can act. If a non-current player attempts
        to act or an illegal action is submitted, handles it cleanly without corrupting state.
        """
        if self.state is None:
            raise RuntimeError("Environment not initialized; call reset() first")

        if self.state.is_terminal:
            raise RuntimeError("Cannot step in a terminal game state")

        curr = self.state.current_player
        actor = acting_player if acting_player is not None else curr

        # Strict current-player turn enforcement
        if actor != curr:
            illegal_event = Event(
                event_type=EventType.ILLEGAL_ACTION,
                timestep=self.state.timestep,
                player=actor,
                details={"reason": f"Player {actor} attempted to act out of turn (current is {curr})"},
            )
            self.history.append(illegal_event)
            self.metrics_collector.record_event(illegal_event)
            raise IllegalActionError(f"Player {actor} cannot act: current player is {curr}")

        # Execute action through EffectResolver
        try:
            step_result = EffectResolver.apply_action(self.state, action)
        except IllegalActionError as e:
            illegal_event = Event(
                event_type=EventType.ILLEGAL_ACTION,
                timestep=self.state.timestep,
                player=curr,
                details={"action": str(action), "reason": str(e)},
            )
            self.history.append(illegal_event)
            self.metrics_collector.record_event(illegal_event)
            raise

        # Accumulate events into history and metrics
        for event in step_result.events:
            self.history.append(event)
            self.metrics_collector.record_event(event)

        # Check if finalized
        if step_result.terminated or step_result.truncated:
            final_hand_sizes = {p: len(cards) for p, cards in self.state.hands.items()}
            self.metrics_collector.finalize(
                winner=self.state.winner,
                terminated=step_result.terminated,
                truncated=step_result.truncated,
                timestep=self.state.timestep,
                turn_count=self.state.turn_count,
                final_hand_sizes=final_hand_sizes,
            )

        # Build observation for the next acting player
        next_obs = self.observe(step_result.next_player)

        info = {
            "events": step_result.events,
            "acting_player": actor,
            "next_player": step_result.next_player,
            "metrics": self.metrics_collector.metrics,
        }

        return EnvStepResult(
            observation=next_obs,
            rewards=step_result.rewards,
            terminated=step_result.terminated,
            truncated=step_result.truncated,
            info=info,
            acting_player=actor,
            next_player=step_result.next_player,
        )

    def get_full_state(self) -> GameState:
        """Researcher/debug interface only. Exposes full underlying GameState."""
        if self.state is None:
            raise RuntimeError("Environment not initialized; call reset() first")
        return self.state

    def serialize_state(self) -> Dict[str, Any]:
        """Serialize current environment state for checkpointing."""
        if self.state is None:
            raise RuntimeError("Environment not initialized; call reset() first")
        return serialize_state(self.state)

    def restore_state(self, serialized_state: Dict[str, Any]) -> None:
        """Restore environment state exactly from serialized dictionary."""
        self.state = restore_state(serialized_state)
        self.config = self.state.config
