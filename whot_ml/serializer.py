"""Deterministic State Serialization and Restoration for WHOT-ML (P0-D4 Section 39)."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from whot_ml.card import (
    CANONICAL_CARD_BY_ID,
    Card,
    Shape,
    SpecialEffect,
)
from whot_ml.invariants import InvariantValidator
from whot_ml.rng_manager import RNGManager
from whot_ml.ruleset import TurnDirection, WHOTConfig
from whot_ml.state import GameState
from whot_ml.turn_manager import TurnModifier
from whot_ml.version import SIMULATOR_VERSION


def serialize_state(state: GameState) -> Dict[str, Any]:
    """Serialize complete ground-truth GameState into a JSON-serializable dictionary.

    Contains complete information to resume the game bitwise deterministically.
    """
    return {
        "version": SIMULATOR_VERSION,
        "episode_id": state.episode_id,
        "timestep": state.timestep,
        "turn_count": state.turn_count,
        "ruleset": state.config.to_dict(),
        "current_player": state.current_player,
        "turn_direction": state.turn_direction.value,
        "current_call": state.current_call.value,
        "active_penalty_type": (
            state.active_penalty_type.value if state.active_penalty_type else None
        ),
        "active_penalty_count": state.active_penalty_count,
        "turn_modifier": state.turn_modifier.value,
        "last_card_declared": {str(k): v for k, v in state.last_card_declared.items()},
        "hands": {
            str(p): [card.id for card in cards]
            for p, cards in state.hands.items()
        },
        "play_pile": [card.id for card in state.play_pile],
        "market": [card.id for card in state.market],
        "rng_state": state.rng_manager.get_state(),
        "is_terminal": state.is_terminal,
        "winner": state.winner,
    }


def restore_state(data: Dict[str, Any]) -> GameState:
    """Reconstruct exact GameState from serialized dictionary."""
    cfg = WHOTConfig.from_dict(data["ruleset"])

    # Reconstruct cards from canonical pool
    hands: Dict[int, List[Card]] = {
        int(p): [CANONICAL_CARD_BY_ID[cid] for cid in card_ids]
        for p, card_ids in data["hands"].items()
    }
    play_pile: List[Card] = [CANONICAL_CARD_BY_ID[cid] for cid in data["play_pile"]]
    market: List[Card] = [CANONICAL_CARD_BY_ID[cid] for cid in data["market"]]

    # Reconstruct RNG
    rng = RNGManager()
    # Python random getstate returns a tuple where the second element is a tuple of ints
    raw_rng = data["rng_state"]
    if isinstance(raw_rng, list):
        # Convert JSON list back to tuple format expected by random.setstate
        version, state_list, gauss = raw_rng
        rng_state = (version, tuple(state_list), gauss)
    else:
        rng_state = tuple(raw_rng)
    rng.set_state(rng_state)

    penalty_type = (
        SpecialEffect(data["active_penalty_type"])
        if data.get("active_penalty_type")
        else None
    )

    state = GameState(
        config=cfg,
        hands=hands,
        market=market,
        play_pile=play_pile,
        current_call=Shape(data["current_call"]),
        current_player=data["current_player"],
        turn_direction=TurnDirection(data["turn_direction"]),
        active_penalty_type=penalty_type,
        active_penalty_count=data["active_penalty_count"],
        turn_modifier=TurnModifier(data["turn_modifier"]),
        last_card_declared={int(k): v for k, v in data["last_card_declared"].items()},
        timestep=data["timestep"],
        turn_count=data["turn_count"],
        episode_id=data["episode_id"],
        rng_manager=rng,
        is_terminal=data["is_terminal"],
        winner=data["winner"],
    )

    if cfg.debug_mode:
        InvariantValidator.validate(state)

    return state


def serialize_to_json(state: GameState) -> str:
    """Serialize GameState to a JSON formatted string."""
    return json.dumps(serialize_state(state), indent=2)


def restore_from_json(json_str: str) -> GameState:
    """Restore GameState from a JSON string."""
    return restore_state(json.loads(json_str))
