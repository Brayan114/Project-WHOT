"""Observation Encoder for WHOT-ML Paper 2 (P2-D1 Section B).

Encodes a raw PlayerObservation into a 280-dimensional feature tensor strictly
respecting the information boundary (zero access to GameState).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple
import torch

from whot_ml.card import (
    CANONICAL_CARD_BY_ID,
    Shape,
    SpecialEffect,
    TOTAL_DECK_SIZE,
)
from whot_ml.event import Event, EventType
from whot_ml.observation import PlayerObservation

# Feature dimensions matching P2-D1 Section B
OBS_FEATURE_DIM = 204
ACTION_MASK_DIM = 76
D_FF = OBS_FEATURE_DIM + ACTION_MASK_DIM  # 280

# Canonical ordering for categorical features
SHAPES_ORDER: Tuple[Shape, ...] = (
    Shape.CIRCLE,
    Shape.TRIANGLE,
    Shape.CROSS,
    Shape.SQUARE,
    Shape.STAR,
    Shape.WHOT,
)

PENALTY_EFFECTS_ORDER: Tuple[Optional[SpecialEffect], ...] = (
    None,
    SpecialEffect.HOLD_ON,
    SpecialEffect.PICK_TWO,
    SpecialEffect.PICK_THREE,
    SpecialEffect.SUSPENSION,
    SpecialEffect.GENERAL_MARKET,
)


class FeedforwardEncoder:
    """Encodes a PlayerObservation into a D_FF = 280 dimensional torch.Tensor.
    
    Structure:
      [0:54]     Own hand composition (54-dim multi-hot)
      [54:108]   Top discard card (54-dim one-hot)
      [108:114]  Current call shape (6-dim one-hot)
      [114:120]  Active penalty type (6-dim one-hot: None, HOLD_ON, PICK_TWO, PICK_THREE, SUSPENSION, GENERAL_MARKET)
      [120:121]  Active penalty count (1-dim normalized scalar: min(count, 10)/10.0)
      [121:125]  Player hand sizes relative to self: self, next, across, previous (4-dim normalized: count/54.0)
      [125:129]  Last card declarations relative to self: self, next, across, previous (4-dim binary)
      [129:130]  Market deck size (1-dim normalized scalar: count/54.0)
      [130:134]  Turn context (4-dim: normalized step count min(t, 1000)/1000.0, relative acting seat 1..3)
      [134:204]  Public discard history (Window K=5, 14 dims/slot = 70-dim dense)
      [204:280]  Legal action mask (76-dim binary)
      
    Total dimension: 280
    """

    def __init__(self, num_players: int = 4, history_window: int = 5) -> None:
        self.num_players = num_players
        self.history_window = history_window
        self.total_dim = D_FF

    def encode(self, obs: PlayerObservation) -> torch.Tensor:
        """Encode a PlayerObservation into a 1D float32 tensor of shape (280,)."""
        vec = torch.zeros(self.total_dim, dtype=torch.float32)

        # 1. Own Hand Composition (54 dims: [0:54])
        for card in obs.hand:
            vec[card.card_index] = 1.0

        # 2. Top Discard Card (54 dims: [54:108])
        if obs.play_pile:
            top_card = obs.top_card
            vec[54 + top_card.card_index] = 1.0

        # 3. Current Call Shape (6 dims: [108:114])
        if obs.current_call in SHAPES_ORDER:
            shape_idx = SHAPES_ORDER.index(obs.current_call)
            vec[108 + shape_idx] = 1.0

        # 4. Active Penalty Type (6 dims: [114:120])
        if obs.active_penalty_type in PENALTY_EFFECTS_ORDER:
            pen_idx = PENALTY_EFFECTS_ORDER.index(obs.active_penalty_type)
            vec[114 + pen_idx] = 1.0

        # 5. Active Penalty Count (1 dim: [120:121])
        vec[120] = min(float(obs.active_penalty_count), 10.0) / 10.0

        # 6. Player Hand Sizes (4 dims: [121:125])
        # Relative to self: self (0), next (1), across (2), previous (3)
        for r in range(self.num_players):
            seat = (obs.player_id + r) % self.num_players
            size = obs.hand_sizes.get(seat, 0)
            vec[121 + r] = min(float(size), 54.0) / 54.0

        # 7. Last Card Declarations (4 dims: [125:129])
        for r in range(self.num_players):
            seat = (obs.player_id + r) % self.num_players
            declared = obs.last_card_declared.get(seat, False)
            vec[125 + r] = 1.0 if declared else 0.0

        # 8. Market Deck Size (1 dim: [129:130])
        vec[129] = min(float(obs.market_size), 54.0) / 54.0

        # 9. Turn Context (4 dims: [130:134])
        # [130]: Normalized turn count min(turn_count, 1000) / 1000.0
        vec[130] = min(float(obs.turn_count), 1000.0) / 1000.0
        # [131:134]: Relative acting seat offset (1, 2, 3) relative to self
        rel_acting = (obs.current_player - obs.player_id) % self.num_players
        if 1 <= rel_acting <= 3:
            vec[130 + rel_acting] = 1.0
        # (rel_acting == 0 means self is acting; slots 131..133 remain 0.0)

        # 10. Public Discard Card History Window K=5 (70 dims: [134:204])
        # Each slot: 14 dims = Shape(6) + NormVal(1) + RelPlayer(4) + Declared(1) + ActionType(2)
        played_events = [e for e in obs.public_history if e.event_type == EventType.CARD_PLAYED]
        recent_events = played_events[-self.history_window:] if len(played_events) >= self.history_window else played_events
        pad_count = self.history_window - len(recent_events)

        for i, evt in enumerate(recent_events):
            slot_idx = pad_count + i
            slot_offset = 134 + slot_idx * 14

            shape: Optional[Shape] = None
            val: int = 0
            is_whot: bool = False

            if evt.card_id and evt.card_id in CANONICAL_CARD_BY_ID:
                c = CANONICAL_CARD_BY_ID[evt.card_id]
                shape = c.shape
                val = c.value
                is_whot = c.is_whot
            elif evt.shape:
                shape = evt.shape

            # Shape one-hot (6)
            if shape in SHAPES_ORDER:
                vec[slot_offset + SHAPES_ORDER.index(shape)] = 1.0

            # Normalized value (1)
            vec[slot_offset + 6] = float(val) / 20.0

            # Acting relative player (4)
            if evt.player is not None:
                rel_player = (evt.player - obs.player_id) % self.num_players
                if 0 <= rel_player < 4:
                    vec[slot_offset + 7 + rel_player] = 1.0

            # Declared flag (1)
            declared_flag = evt.details.get("declared", False)
            if not declared_flag and evt.player is not None:
                declared_flag = obs.last_card_declared.get(evt.player, False)
            vec[slot_offset + 11] = 1.0 if declared_flag else 0.0

            # Action type (2): [1.0, 0.0] ordinary, [0.0, 1.0] WHOT
            if is_whot:
                vec[slot_offset + 13] = 1.0
            else:
                vec[slot_offset + 12] = 1.0

        # 11. Legal Action Mask (76 dims: [204:280])
        mask_tensor = torch.tensor(obs.action_mask, dtype=torch.float32)
        vec[204:280] = mask_tensor

        return vec

    def __call__(self, obs: PlayerObservation) -> torch.Tensor:
        return self.encode(obs)
