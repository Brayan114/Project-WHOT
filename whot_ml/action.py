"""Frozen 76-Action Space definition and bidirectional mappings for WHOT-ML.

Action Index Specification (Frozen as required):
  - 0–48:  PLAY ordinary physical cards (the 49 ordinary cards in canonical order)
  - 49–73: PLAY WHOT card with selected shape
           5 WHOT cards (indices 49–53) × 5 ordinary shapes (CIRCLE, TRIANGLE, CROSS, SQUARE, STAR)
           Formula: 49 + (whot_index - 49) * 5 + shape_offset
  - 74:    DRAW
  - 75:    DECLARE_LAST
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple

from whot_ml.card import (
    CANONICAL_CARD_BY_INDEX,
    CANONICAL_DECK,
    NUM_ORDINARY_CARDS,
    NUM_WHOT_CARDS,
    Card,
    CardType,
    Shape,
)


class ActionType(str, Enum):
    """The four action categories in baseline WHOT-NG-v1."""
    PLAY = "PLAY"
    PLAY_WHOT = "PLAY_WHOT"
    DRAW = "DRAW"
    DECLARE_LAST = "DECLARE_LAST"


TOTAL_ACTIONS = 76
ACTION_INDEX_DRAW = 74
ACTION_INDEX_DECLARE_LAST = 75
ORDINARY_SHAPES: Tuple[Shape, ...] = Shape.ordinary_shapes()


@dataclass(frozen=True)
class Action:
    """An explicit, structured action object for WHOT-ML."""
    action_type: ActionType
    action_id: int
    card_id: Optional[str] = None
    card_index: Optional[int] = None
    selected_shape: Optional[Shape] = None

    def __post_init__(self) -> None:
        if not (0 <= self.action_id < TOTAL_ACTIONS):
            raise ValueError(f"action_id must be in [0, {TOTAL_ACTIONS - 1}], got {self.action_id}")

        if self.action_type == ActionType.PLAY:
            if self.card_id is None or self.card_index is None:
                raise ValueError("PLAY action must specify card_id and card_index")
            if not (0 <= self.card_index < NUM_ORDINARY_CARDS):
                raise ValueError(f"Ordinary PLAY card_index must be < {NUM_ORDINARY_CARDS}")
            if self.selected_shape is not None:
                raise ValueError("Ordinary PLAY must not have selected_shape")
            if self.action_id != self.card_index:
                raise ValueError(f"PLAY action_id {self.action_id} must equal card_index {self.card_index}")

        elif self.action_type == ActionType.PLAY_WHOT:
            if self.card_id is None or self.card_index is None:
                raise ValueError("PLAY_WHOT action must specify card_id and card_index")
            if not (NUM_ORDINARY_CARDS <= self.card_index < NUM_ORDINARY_CARDS + NUM_WHOT_CARDS):
                raise ValueError("PLAY_WHOT card_index must be a valid WHOT card")
            if self.selected_shape is None or not self.selected_shape.is_ordinary:
                raise ValueError(f"PLAY_WHOT requires an ordinary selected shape, got {self.selected_shape}")
            whot_offset = self.card_index - NUM_ORDINARY_CARDS
            shape_offset = ORDINARY_SHAPES.index(self.selected_shape)
            expected_id = NUM_ORDINARY_CARDS + whot_offset * len(ORDINARY_SHAPES) + shape_offset
            if self.action_id != expected_id:
                raise ValueError(f"PLAY_WHOT action_id {self.action_id} != expected {expected_id}")

        elif self.action_type == ActionType.DRAW:
            if self.action_id != ACTION_INDEX_DRAW:
                raise ValueError(f"DRAW action_id must be {ACTION_INDEX_DRAW}")
            if self.card_id is not None or self.selected_shape is not None:
                raise ValueError("DRAW action must not have card or shape")

        elif self.action_type == ActionType.DECLARE_LAST:
            if self.action_id != ACTION_INDEX_DECLARE_LAST:
                raise ValueError(f"DECLARE_LAST action_id must be {ACTION_INDEX_DECLARE_LAST}")
            if self.card_id is not None or self.selected_shape is not None:
                raise ValueError("DECLARE_LAST action must not have card or shape")

    def __str__(self) -> str:
        if self.action_type == ActionType.PLAY:
            return f"Action(PLAY {self.card_id} [id={self.action_id}])"
        elif self.action_type == ActionType.PLAY_WHOT:
            return f"Action(PLAY_WHOT {self.card_id} -> {self.selected_shape.value} [id={self.action_id}])"
        elif self.action_type == ActionType.DRAW:
            return f"Action(DRAW [id={self.action_id}])"
        elif self.action_type == ActionType.DECLARE_LAST:
            return f"Action(DECLARE_LAST [id={self.action_id}])"
        return f"Action(UNKNOWN [id={self.action_id}])"


def _build_action_tables() -> Tuple[Dict[int, Action], Dict[Action, int]]:
    """Construct the canonical bijection between action indices and Action instances."""
    index_to_act: Dict[int, Action] = {}

    # 1. 0 to 48: PLAY ordinary cards
    for card_idx in range(NUM_ORDINARY_CARDS):
        card = CANONICAL_CARD_BY_INDEX[card_idx]
        action = Action(
            action_type=ActionType.PLAY,
            action_id=card_idx,
            card_id=card.id,
            card_index=card_idx,
            selected_shape=None,
        )
        index_to_act[card_idx] = action

    # 2. 49 to 73: PLAY WHOT with selected shape
    for whot_idx in range(NUM_ORDINARY_CARDS, NUM_ORDINARY_CARDS + NUM_WHOT_CARDS):
        card = CANONICAL_CARD_BY_INDEX[whot_idx]
        whot_offset = whot_idx - NUM_ORDINARY_CARDS
        for shape_offset, shape in enumerate(ORDINARY_SHAPES):
            action_id = NUM_ORDINARY_CARDS + whot_offset * len(ORDINARY_SHAPES) + shape_offset
            action = Action(
                action_type=ActionType.PLAY_WHOT,
                action_id=action_id,
                card_id=card.id,
                card_index=whot_idx,
                selected_shape=shape,
            )
            index_to_act[action_id] = action

    # 3. 74: DRAW
    index_to_act[ACTION_INDEX_DRAW] = Action(
        action_type=ActionType.DRAW,
        action_id=ACTION_INDEX_DRAW,
    )

    # 4. 75: DECLARE_LAST
    index_to_act[ACTION_INDEX_DECLARE_LAST] = Action(
        action_type=ActionType.DECLARE_LAST,
        action_id=ACTION_INDEX_DECLARE_LAST,
    )

    assert len(index_to_act) == TOTAL_ACTIONS, f"Expected {TOTAL_ACTIONS} actions, got {len(index_to_act)}"
    act_to_index: Dict[Action, int] = {act: idx for idx, act in index_to_act.items()}
    return index_to_act, act_to_index


INDEX_TO_ACTION, ACTION_TO_INDEX = _build_action_tables()


def index_to_action(action_id: int) -> Action:
    """Retrieve the immutable Action corresponding to an integer action index."""
    if action_id not in INDEX_TO_ACTION:
        raise IndexError(f"Action index must be between 0 and {TOTAL_ACTIONS - 1}, got {action_id}")
    return INDEX_TO_ACTION[action_id]


def action_to_index(action: Action) -> int:
    """Retrieve the integer action index for an Action."""
    return action.action_id


def make_play_card_action(card: Card) -> Action:
    """Create an action to play an ordinary card."""
    if card.card_type != CardType.ORDINARY:
        raise ValueError(f"make_play_card_action only applies to ordinary cards, got {card}")
    return index_to_action(card.card_index)


def make_play_whot_action(card: Card, selected_shape: Shape) -> Action:
    """Create an action to play a WHOT card with a selected ordinary shape."""
    if card.card_type != CardType.WHOT:
        raise ValueError(f"make_play_whot_action only applies to WHOT cards, got {card}")
    if not selected_shape.is_ordinary:
        raise ValueError(f"Selected shape must be ordinary, got {selected_shape}")
    whot_offset = card.card_index - NUM_ORDINARY_CARDS
    shape_offset = ORDINARY_SHAPES.index(selected_shape)
    action_id = NUM_ORDINARY_CARDS + whot_offset * len(ORDINARY_SHAPES) + shape_offset
    return index_to_action(action_id)


def make_draw_action() -> Action:
    """Create the DRAW action."""
    return index_to_action(ACTION_INDEX_DRAW)


def make_declare_last_action() -> Action:
    """Create the DECLARE_LAST action."""
    return index_to_action(ACTION_INDEX_DECLARE_LAST)
