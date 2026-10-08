"""Shared experimental infrastructure for Paper 1 (Stage 3A).

Provides:
- RunManifest for provenance and auditability.
- TrajectoryCollector for neutral, non-mutating step-by-step telemetry.
- BalancedSeatAssigner for position-bias-free tournament play.
- Rigorous statistical utilities (Wilson score CIs, IQR, ECDF, Cliff's delta).
- Serialization and IO helpers for raw, processed, and presentation tiers.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import platform
import statistics
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

from whot_ml.action import Action, action_to_index
from whot_ml.agents.base import Agent
from whot_ml.agents.random_agent import RandomLegalAgent
from whot_ml.agents.rule_based_agent import RuleBasedAgent
from whot_ml.card import TOTAL_DECK_SIZE
from whot_ml.environment import EnvStepResult, GameEnvironment
from whot_ml.event import Event
from whot_ml.ruleset import (
    LastCardViolationPenalty,
    StackingMode,
    StarterPolicy,
    TurnDirection,
    WHOTConfig,
    get_baseline_config,
)
from whot_ml.version import BASELINE_ENVIRONMENT, SIMULATOR_VERSION

# Frozen simulator reference commit
FROZEN_SIMULATOR_COMMIT = "7c1a2dc"


def compute_config_hash(config: WHOTConfig) -> str:
    """Return a deterministic SHA-256 hash of a WHOTConfig."""
    data = config.to_dict()
    serialized = json.dumps(data, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]


@dataclass
class RunManifest:
    """Immutable audit record attached to every experiment run."""
    experiment_id: str
    is_pilot: bool
    seed: int
    player_count: int
    is_dry_run: bool = False
    simulator_version: str = SIMULATOR_VERSION
    simulator_commit: str = FROZEN_SIMULATOR_COMMIT
    baseline_environment: str = BASELINE_ENVIRONMENT
    variant_id: str = "VAR-BASE"
    variant_parent: str = "WHOT-NG-v1"
    ruleset_hash: str = ""
    config_hash: str = ""
    agent_population: List[str] = field(default_factory=list)
    seat_assignment: Dict[int, str] = field(default_factory=dict)
    starting_player: int = 0
    timestamp_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    platform_info: Dict[str, str] = field(
        default_factory=lambda: {
            "os": platform.system(),
            "python_version": sys.version.split()[0],
        }
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StepTelemetry:
    """Per-step observation and transition record."""
    step_idx: int
    turn_idx: int
    player_id: int
    action_type: str
    card_id: Optional[str]
    selected_shape: Optional[str]
    action_index: int
    legal_action_count: int
    acting_hand_size: int
    all_hand_sizes: Dict[int, int]
    market_size: int
    top_card_id: str
    current_call: str
    active_penalty_count: int
    events: List[Dict[str, Any]]
    rewards: Dict[int, float]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GameTrajectoryRecord:
    """Complete game trajectory record containing manifest, steps, and summary."""
    manifest: RunManifest
    steps: List[StepTelemetry] = field(default_factory=list)
    winner: Optional[int] = None
    terminated: bool = False
    truncated: bool = False
    turn_count: int = 0
    timestep: int = 0
    final_hand_sizes: Dict[int, int] = field(default_factory=dict)
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
            "manifest": self.manifest.to_dict(),
            "steps": [s.to_dict() for s in self.steps],
            "summary": {
                "winner": self.winner,
                "terminated": self.terminated,
                "truncated": self.truncated,
                "turn_count": self.turn_count,
                "timestep": self.timestep,
                "final_hand_sizes": {str(k): v for k, v in self.final_hand_sizes.items()},
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
            },
        }


class TrajectoryCollector:
    """Non-mutating telemetry logger wrapping headless game execution.

    Enforces strict information boundaries:
    - Steps and observations are recorded via public GameEnvironment interfaces.
    - Full GameState is only inspected for external card conservation assertions.
    - Zero telemetry state is ever leaked to agents.
    """

    @staticmethod
    def play_instrumented_game(
        env: GameEnvironment,
        agents: Dict[int, Agent],
        manifest: RunManifest,
        record_steps: bool = True,
    ) -> GameTrajectoryRecord:
        """Execute a game with step-by-step telemetry collection and invariant checks."""
        initial_obs = env.reset(seed=manifest.seed)
        manifest.starting_player = env.current_player
        manifest.seat_assignment = {p: agents[p].name for p in range(env.config.player_count)}

        for p, agent in agents.items():
            agent.reset(player_id=p, seed=manifest.seed + p)

        record = GameTrajectoryRecord(manifest=manifest)
        terminated = False
        truncated = False
        step_idx = 0

        # Assert starting card conservation
        state = env.get_full_state()
        initial_cards = len(state.market) + len(state.play_pile) + sum(len(h) for h in state.hands.values())
        if initial_cards != TOTAL_DECK_SIZE:
            raise RuntimeError(f"Card conservation violated at reset: {initial_cards} != {TOTAL_DECK_SIZE}")

        while not (terminated or truncated):
            curr_player = env.current_player
            obs = env.observe(curr_player)
            agent = agents[curr_player]

            legal_actions = obs.legal_actions
            legal_count = len(legal_actions)
            acting_hand_size = len(obs.hand)
            all_hand_sizes = dict(obs.hand_sizes)
            top_card_id = obs.top_card.id
            curr_call = obs.current_call.value
            active_pen = obs.active_penalty_count

            # Agent selects action using only its isolated PlayerObservation
            action = agent.act(obs)
            act_idx = action_to_index(action)

            step_res: EnvStepResult = env.step(action, acting_player=curr_player)

            # Record step telemetry if enabled
            if record_steps:
                events_dicts = [e.to_dict() for e in step_res.info.get("events", [])]
                record.steps.append(
                    StepTelemetry(
                        step_idx=step_idx,
                        turn_idx=env.state.turn_count if env.state else 0,
                        player_id=curr_player,
                        action_type=action.action_type.value,
                        card_id=action.card_id,
                        selected_shape=(
                            action.selected_shape.value if action.selected_shape else None
                        ),
                        action_index=act_idx,
                        legal_action_count=legal_count,
                        acting_hand_size=acting_hand_size,
                        all_hand_sizes=all_hand_sizes,
                        market_size=obs.market_size,
                        top_card_id=top_card_id,
                        current_call=curr_call,
                        active_penalty_count=active_pen,
                        events=events_dicts,
                        rewards=dict(step_res.rewards),
                    )
                )

            # Assert card conservation invariant
            st = env.get_full_state()
            tot = len(st.market) + len(st.play_pile) + sum(len(h) for h in st.hands.values())
            if tot != TOTAL_DECK_SIZE:
                raise RuntimeError(
                    f"Card conservation violated at step {step_idx}: {tot} != {TOTAL_DECK_SIZE}"
                )

            terminated = step_res.terminated
            truncated = step_res.truncated
            step_idx += 1

        # Populate summary from finalized metrics
        ep_m = env.metrics_collector.metrics
        record.winner = ep_m.winner
        record.terminated = ep_m.terminated
        record.truncated = ep_m.truncated
        record.turn_count = ep_m.turn_count
        record.timestep = ep_m.timestep
        record.final_hand_sizes = dict(ep_m.final_hand_sizes)
        record.draw_count = ep_m.draw_count
        record.whot_plays = ep_m.whot_plays
        record.pick_two_plays = ep_m.pick_two_plays
        record.pick_three_plays = ep_m.pick_three_plays
        record.hold_on_plays = ep_m.hold_on_plays
        record.suspensions = ep_m.suspensions
        record.general_market_activations = ep_m.general_market_activations
        record.declaration_violations = ep_m.declaration_violations
        record.market_reshuffles = ep_m.market_reshuffles
        record.draw_unavailable_count = ep_m.draw_unavailable_count
        record.illegal_action_count = ep_m.illegal_action_count

        return record


class BalancedSeatAssigner:
    """Rotates agent positions deterministically across seats to eliminate position bias."""

    @staticmethod
    def assign_seats(
        agent_types: List[str],
        game_index: int,
        base_seed: int,
        rotate: bool = True,
    ) -> Dict[int, Agent]:
        """Construct agents with balanced seating.

        If rotate is True, seats are cyclically shifted by game_index mod N.
        """
        n = len(agent_types)
        agents: Dict[int, Agent] = {}

        for seat in range(n):
            type_idx = (seat - game_index) % n if rotate else seat
            atype = agent_types[type_idx]
            seed = base_seed + game_index * 10 + seat

            if atype == "rule_based":
                agents[seat] = RuleBasedAgent(name=f"RuleBased-Seat{seat}", seed=seed)
            elif atype == "random":
                agents[seat] = RandomLegalAgent(name=f"Random-Seat{seat}", seed=seed)
            else:
                raise ValueError(f"Unknown agent type: {atype}")

        return agents


class StatisticalUtilities:
    """Statistical functions required by Paper 1 experimental protocol."""

    @staticmethod
    def calculate_scalar_stats(values: Sequence[Union[int, float]]) -> Dict[str, Any]:
        """Compute sample size, mean, std, median, IQR [q25, q75], min, max, skewness."""
        if not values:
            return {
                "n": 0,
                "mean": 0.0,
                "std": 0.0,
                "median": 0.0,
                "q25": 0.0,
                "q75": 0.0,
                "iqr": 0.0,
                "min": 0.0,
                "max": 0.0,
                "skewness": 0.0,
            }

        n = len(values)
        vals = sorted(float(v) for v in values)
        mean_val = statistics.mean(vals)
        std_val = statistics.stdev(vals) if n > 1 else 0.0
        med_val = statistics.median(vals)

        # 25th and 75th percentiles
        def percentile(data: List[float], p: float) -> float:
            k = (len(data) - 1) * p
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return data[int(k)]
            d0 = data[int(f)] * (c - k)
            d1 = data[int(c)] * (k - f)
            return d0 + d1

        q25 = percentile(vals, 0.25)
        q75 = percentile(vals, 0.75)
        iqr_val = q75 - q25

        # Fisher-Pearson sample skewness
        if n > 2 and std_val > 1e-9:
            skew_val = (
                (n / ((n - 1) * (n - 2)))
                * sum(((x - mean_val) / std_val) ** 3 for x in vals)
            )
        else:
            skew_val = 0.0

        return {
            "n": n,
            "mean": round(mean_val, 4),
            "std": round(std_val, 4),
            "median": round(med_val, 4),
            "q25": round(q25, 4),
            "q75": round(q75, 4),
            "iqr": round(iqr_val, 4),
            "min": round(vals[0], 4),
            "max": round(vals[-1], 4),
            "skewness": round(skew_val, 4),
        }

    @staticmethod
    def wilson_score_interval(
        successes: int, total: int, confidence: float = 0.95
    ) -> Dict[str, Any]:
        """Compute Wilson score continuity-corrected confidence interval for a proportion."""
        if total <= 0:
            return {"point": 0.0, "ci_lower": 0.0, "ci_upper": 0.0, "confidence": confidence}

        p_hat = successes / total
        z = 1.95996 if confidence == 0.95 else 2.57583  # standard normal quantile

        denominator = 1.0 + (z ** 2) / total
        centre_adj = p_hat + (z ** 2) / (2.0 * total)
        radius = z * math.sqrt(
            (p_hat * (1.0 - p_hat) + (z ** 2) / (4.0 * total)) / total
        )

        ci_lower = max(0.0, (centre_adj - radius) / denominator)
        ci_upper = min(1.0, (centre_adj + radius) / denominator)

        return {
            "point": round(p_hat, 4),
            "ci_lower": round(ci_lower, 4),
            "ci_upper": round(ci_upper, 4),
            "confidence": confidence,
        }

    @staticmethod
    def compute_ecdf(values: Sequence[Union[int, float]]) -> List[Dict[str, float]]:
        """Compute Empirical Cumulative Distribution Function."""
        if not values:
            return []
        vals = sorted(float(v) for v in values)
        n = len(vals)
        ecdf = []
        for i, v in enumerate(vals):
            ecdf.append({"x": v, "y": round((i + 1) / n, 4)})
        return ecdf

    @staticmethod
    def cliffs_delta(x: Sequence[float], y: Sequence[float]) -> float:
        """Calculate Cliff's delta non-parametric effect size between distributions x and y."""
        if not x or not y:
            return 0.0
        n_x, n_y = len(x), len(y)
        more = sum(1 for xi in x for yj in y if xi > yj)
        less = sum(1 for xi in x for yj in y if xi < yj)
        return round((more - less) / (n_x * n_y), 4)

    @staticmethod
    def paired_differences(
        baseline: Sequence[float], variant: Sequence[float]
    ) -> Dict[str, Any]:
        """Calculate paired differences and Wilcoxon signed-rank statistic."""
        if len(baseline) != len(variant) or not baseline:
            raise ValueError("Baseline and variant must have equal non-zero lengths")

        diffs = [v - b for b, v in zip(baseline, variant)]
        stats = StatisticalUtilities.calculate_scalar_stats(diffs)

        # Non-zero differences for Wilcoxon
        non_zero = [d for d in diffs if abs(d) > 1e-9]
        if non_zero:
            ranks = sorted(range(len(non_zero)), key=lambda i: abs(non_zero[i]))
            w_plus = sum(
                r + 1 for r, i in enumerate(ranks) if non_zero[i] > 0
            )
            w_minus = sum(
                r + 1 for r, i in enumerate(ranks) if non_zero[i] < 0
            )
            w_stat = min(w_plus, w_minus)
        else:
            w_stat = 0

        stats["wilson_w"] = w_stat
        return stats


class ExperimentPaths:
    """Standardized paths for Paper 1 experimental artifacts."""

    ROOT = Path(os.environ.get("WHOT_ROOT", Path(__file__).resolve().parents[3]))
    PAPER1 = Path(os.environ.get("WHOT_PAPER1_DIR", ROOT / "experiments" / "paper1"))
    CONFIGS = PAPER1 / "configs"
    SCRIPTS = PAPER1 / "scripts"
    RAW = PAPER1 / "raw"
    PROCESSED = PAPER1 / "processed"
    FIGURES = PAPER1 / "figures"
    TABLES = PAPER1 / "tables"
    REPORTS = PAPER1 / "reports"
    RUNS = PAPER1 / "runs"

    @classmethod
    def set_run_directory(cls, run_dir: Union[str, Path]) -> None:
        """Dynamically redirect output directories to an isolated run directory (e.g. for dry runs or Kaggle)."""
        run_path = Path(run_dir)
        cls.RAW = run_path / "raw"
        cls.PROCESSED = run_path / "processed"
        cls.FIGURES = run_path / "figures"
        cls.TABLES = run_path / "tables"
        cls.REPORTS = run_path / "reports"
        cls.ensure_directories()

    @classmethod
    def reset_paths(cls) -> None:
        """Reset output directories back to standard locations."""
        cls.RAW = cls.PAPER1 / "raw"
        cls.PROCESSED = cls.PAPER1 / "processed"
        cls.FIGURES = cls.PAPER1 / "figures"
        cls.TABLES = cls.PAPER1 / "tables"
        cls.REPORTS = cls.PAPER1 / "reports"

    @classmethod
    def ensure_directories(cls) -> None:
        """Create all required experiment directories if they do not exist."""
        for d in (
            cls.CONFIGS,
            cls.SCRIPTS,
            cls.RAW,
            cls.PROCESSED,
            cls.FIGURES,
            cls.TABLES,
            cls.REPORTS,
            cls.RUNS,
        ):
            d.mkdir(parents=True, exist_ok=True)


class StreamTelemetryWriter:
    """Context manager for streaming incremental JSONL records directly to disk."""

    def __init__(self, filename: str):
        ExperimentPaths.ensure_directories()
        self.filepath = ExperimentPaths.RAW / filename
        self._file = None

    def __enter__(self) -> "StreamTelemetryWriter":
        self._file = open(self.filepath, "w", encoding="utf-8")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._file:
            self._file.close()

    def write_record(self, record: Union[GameTrajectoryRecord, Dict[str, Any]]) -> None:
        """Write and flush a single trajectory record to disk incrementally."""
        if self._file is None:
            raise RuntimeError("StreamTelemetryWriter must be used as a context manager.")
        data = record.to_dict() if hasattr(record, "to_dict") else record
        self._file.write(json.dumps(data) + "\n")
        self._file.flush()


def load_experiment_config(config_filename: str) -> Dict[str, Any]:
    """Load an experiment configuration JSON file."""
    path = ExperimentPaths.CONFIGS / config_filename
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_raw_telemetry(filename: str, records: List[GameTrajectoryRecord]) -> Path:
    """Save raw trajectory records to a JSONL file."""
    ExperimentPaths.ensure_directories()
    path = ExperimentPaths.RAW / filename
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r.to_dict()) + "\n")
    return path


def save_processed_metrics(filename: str, data: Dict[str, Any]) -> Path:
    """Save derived metrics to a formatted JSON file."""
    ExperimentPaths.ensure_directories()
    path = ExperimentPaths.PROCESSED / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path
