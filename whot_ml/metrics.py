"""Metrics collection for WHOT-ML experimental evaluation (P0-D4 Section 49, P0-D5)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from whot_ml.event import Event, EventType


@dataclass
class EpisodeMetrics:
    """Detailed metrics recorded for a single game episode."""
    episode_id: str
    winner: Optional[int] = None
    terminated: bool = False
    truncated: bool = False
    turn_count: int = 0
    timestep: int = 0
    final_hand_sizes: Dict[int, int] = field(default_factory=dict)
    finishing_positions: List[int] = field(default_factory=list)
    draw_count: int = 0
    whot_plays: int = 0
    pick_two_plays: int = 0
    pick_three_plays: int = 0
    hold_on_plays: int = 0
    suspensions: int = 0
    general_market_activations: int = 0
    declaration_violations: int = 0
    market_reshuffles: int = 0
    draw_unavailable_count: int = 0
    illegal_action_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "winner": self.winner,
            "terminated": self.terminated,
            "truncated": self.truncated,
            "turn_count": self.turn_count,
            "timestep": self.timestep,
            "final_hand_sizes": {str(k): v for k, v in self.final_hand_sizes.items()},
            "finishing_positions": list(self.finishing_positions),
            "draw_count": self.draw_count,
            "whot_plays": self.whot_plays,
            "pick_two_plays": self.pick_two_plays,
            "pick_three_plays": self.pick_three_plays,
            "hold_on_plays": self.hold_on_plays,
            "suspensions": self.suspensions,
            "general_market_activations": self.general_market_activations,
            "declaration_violations": self.declaration_violations,
            "market_reshuffles": self.market_reshuffles,
            "draw_unavailable_count": self.draw_unavailable_count,
            "illegal_action_count": self.illegal_action_count,
        }


class MetricsCollector:
    """Collects and aggregates gameplay metrics from simulator events and transitions."""

    def __init__(self, episode_id: str = "") -> None:
        self.metrics = EpisodeMetrics(episode_id=episode_id)

    def record_event(self, event: Event) -> None:
        """Update metrics in response to an emitted event."""
        et = event.event_type
        if et == EventType.CARD_DRAWN:
            self.metrics.draw_count += 1
        elif et == EventType.WHOT_SHAPE_SELECTED:
            self.metrics.whot_plays += 1
        elif et == EventType.PENALTY_ACTIVATED or et == EventType.PENALTY_STACKED:
            # Check details or penalty count
            p_count = event.penalty_count
            if p_count is not None and p_count % 3 == 0:
                self.metrics.pick_three_plays += 1
            else:
                self.metrics.pick_two_plays += 1
        elif et == EventType.HOLD_ON_ACTIVATED:
            self.metrics.hold_on_plays += 1
        elif et == EventType.TURN_SKIPPED:
            self.metrics.suspensions += 1
        elif et == EventType.GENERAL_MARKET_ACTIVATED:
            self.metrics.general_market_activations += 1
        elif et == EventType.LAST_CARD_DECLARATION_VIOLATION:
            self.metrics.declaration_violations += 1
        elif et == EventType.MARKET_RESHUFFLED:
            self.metrics.market_reshuffles += 1
        elif et == EventType.DRAW_UNAVAILABLE:
            self.metrics.draw_unavailable_count += 1
        elif et == EventType.ILLEGAL_ACTION:
            self.metrics.illegal_action_count += 1

    def finalize(
        self,
        winner: Optional[int],
        terminated: bool,
        truncated: bool,
        timestep: int,
        turn_count: int,
        final_hand_sizes: Dict[int, int],
    ) -> EpisodeMetrics:
        """Finalize metrics at end of episode."""
        self.metrics.winner = winner
        self.metrics.terminated = terminated
        self.metrics.truncated = truncated
        self.metrics.timestep = timestep
        self.metrics.turn_count = turn_count
        self.metrics.final_hand_sizes = dict(final_hand_sizes)

        # Compute finishing positions sorted by hand size ascending
        sorted_players = sorted(final_hand_sizes.keys(), key=lambda p: final_hand_sizes[p])
        self.metrics.finishing_positions = sorted_players

        return self.metrics


@dataclass
class BatchMetrics:
    """Aggregated metrics across a multi-game evaluation run."""
    games_played: int
    wins_by_player: Dict[int, int]
    win_rates: Dict[int, float]
    truncations: int
    average_game_length: float
    average_hand_size: float
    total_declaration_violations: int
    total_illegal_actions: int

    def summary(self) -> str:
        lines = [
            f"=== BATCH EVALUATION SUMMARY ({self.games_played} Games) ===",
            f"  Wins by Player: {self.wins_by_player}",
            f"  Win Rates: { {p: f'{r:.1%}' for p, r in self.win_rates.items()} }",
            f"  Avg Game Length: {self.average_game_length:.2f} turns",
            f"  Avg Final Hand Size: {self.average_hand_size:.2f}",
            f"  Truncated Games: {self.truncations}",
            f"  Declaration Violations: {self.total_declaration_violations}",
            f"  Illegal Actions: {self.total_illegal_actions}",
        ]
        return "\n".join(lines)


def aggregate_metrics(episode_list: List[EpisodeMetrics], player_count: int = 4) -> BatchMetrics:
    """Compute aggregate statistical summary from a list of EpisodeMetrics."""
    total_games = len(episode_list)
    if total_games == 0:
        return BatchMetrics(
            games_played=0,
            wins_by_player={p: 0 for p in range(player_count)},
            win_rates={p: 0.0 for p in range(player_count)},
            truncations=0,
            average_game_length=0.0,
            average_hand_size=0.0,
            total_declaration_violations=0,
            total_illegal_actions=0,
        )

    wins: Dict[int, int] = {p: 0 for p in range(player_count)}
    truncations = 0
    total_turns = 0
    all_hand_sizes: List[int] = []
    total_violations = 0
    total_illegal = 0

    for ep in episode_list:
        if ep.winner is not None:
            wins[ep.winner] = wins.get(ep.winner, 0) + 1
        if ep.truncated:
            truncations += 1
        total_turns += ep.turn_count
        for sz in ep.final_hand_sizes.values():
            all_hand_sizes.append(sz)
        total_violations += ep.declaration_violations
        total_illegal += ep.illegal_action_count

    win_rates = {p: wins.get(p, 0) / total_games for p in range(player_count)}
    avg_length = total_turns / total_games
    avg_hand = (sum(all_hand_sizes) / len(all_hand_sizes)) if all_hand_sizes else 0.0

    return BatchMetrics(
        games_played=total_games,
        wins_by_player=wins,
        win_rates=win_rates,
        truncations=truncations,
        average_game_length=avg_length,
        average_hand_size=avg_hand,
        total_declaration_violations=total_violations,
        total_illegal_actions=total_illegal,
    )
