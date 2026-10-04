"""Test helper utilities for constructing valid, invariant-compliant test states."""

from __future__ import annotations

from typing import Dict, List, Optional

from whot_ml.card import CANONICAL_CARD_BY_ID, CANONICAL_DECK, Card, Shape, SpecialEffect
from whot_ml.invariants import InvariantValidator
from whot_ml.rng_manager import RNGManager
from whot_ml.ruleset import WHOTConfig, get_baseline_config
from whot_ml.state import GameState
from whot_ml.turn_manager import TurnModifier


def make_custom_state(
    current_player: int = 0,
    hands: Optional[Dict[int, List[Card]]] = None,
    play_pile: Optional[List[Card]] = None,
    current_call: Optional[Shape] = None,
    active_penalty_type: Optional[SpecialEffect] = None,
    active_penalty_count: int = 0,
    turn_modifier: TurnModifier = TurnModifier.NORMAL,
    last_card_declared: Optional[Dict[int, bool]] = None,
    config: Optional[WHOTConfig] = None,
    seed: int = 42,
) -> GameState:
    """Create a completely valid GameState with specified cards, placing remaining cards in market.

    Guarantees strict card conservation (54 cards) and uniqueness.
    """
    cfg = config if config is not None else get_baseline_config()
    rng = RNGManager(seed)

    if play_pile is None:
        play_pile = [CANONICAL_CARD_BY_ID["CIRCLE_4"]]
    else:
        play_pile = list(play_pile)

    if hands is None:
        hands = {p: [] for p in range(cfg.player_count)}
    else:
        hands = {p: list(cards) for p, cards in hands.items()}
        for p in range(cfg.player_count):
            if p not in hands:
                hands[p] = []

    used_cards = set(play_pile)
    for p_cards in hands.values():
        for c in p_cards:
            if c in used_cards:
                raise ValueError(f"Card {c.id} appears multiple times in custom setup")
            used_cards.add(c)

    # All unassigned canonical cards become the market
    market = [c for c in CANONICAL_DECK if c not in used_cards]

    call = current_call
    if call is None:
        call = play_pile[-1].shape if play_pile[-1].shape.is_ordinary else Shape.CIRCLE

    declared = (
        dict(last_card_declared)
        if last_card_declared is not None
        else {p: False for p in range(cfg.player_count)}
    )

    state = GameState(
        config=cfg,
        hands=hands,
        market=market,
        play_pile=play_pile,
        current_call=call,
        current_player=current_player,
        turn_direction=cfg.turn_direction,
        active_penalty_type=active_penalty_type,
        active_penalty_count=active_penalty_count,
        turn_modifier=turn_modifier,
        last_card_declared=declared,
        timestep=0,
        turn_count=0,
        rng_manager=rng,
        is_terminal=False,
        winner=None,
    )
    if cfg.debug_mode:
        InvariantValidator.validate(state)

    return state
