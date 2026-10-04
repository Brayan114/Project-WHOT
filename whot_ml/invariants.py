"""State Invariant validation for WHOT-ML (P0-D4 Section 40)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from whot_ml.card import TOTAL_DECK_SIZE, Shape

if TYPE_CHECKING:
    from whot_ml.state import GameState


class InvariantViolationError(AssertionError):
    """Raised when an internal state invariant fails in debug/test mode."""

    def __init__(
        self,
        failed_invariant: str,
        episode_id: str,
        timestep: int,
        ruleset_name: str,
        diagnostic_details: str,
    ) -> None:
        self.failed_invariant = failed_invariant
        self.episode_id = episode_id
        self.timestep = timestep
        self.ruleset_name = ruleset_name
        self.diagnostic_details = diagnostic_details
        message = (
            f"\n[INVARIANT VIOLATION] {failed_invariant}\n"
            f"  Episode: {episode_id}\n"
            f"  Timestep: {timestep}\n"
            f"  Ruleset: {ruleset_name}\n"
            f"  Diagnostics:\n{diagnostic_details}"
        )
        super().__init__(message)


class InvariantValidator:
    """Validates game state invariants after every action in debug mode."""

    @classmethod
    def validate(cls, state: GameState) -> None:
        """Run all invariant checks on the given GameState.

        Raises InvariantViolationError with detailed diagnostic information upon failure.
        """
        diagnostic_lines: List[str] = []

        def fail(inv_name: str) -> None:
            summary = "\n".join(diagnostic_lines)
            raise InvariantViolationError(
                failed_invariant=inv_name,
                episode_id=state.episode_id,
                timestep=state.timestep,
                ruleset_name=state.config.ruleset_name,
                diagnostic_details=summary,
            )

        # Record summary for diagnostics
        diagnostic_lines.append(f"  Current Player: {state.current_player}")
        diagnostic_lines.append(f"  Current Call: {state.current_call}")
        diagnostic_lines.append(f"  Top Card: {state.top_card}")
        diagnostic_lines.append(f"  Market Count: {len(state.market)}")
        diagnostic_lines.append(f"  Play Pile Count: {len(state.play_pile)}")
        hand_counts = {p: len(cards) for p, cards in state.hands.items()}
        diagnostic_lines.append(f"  Hand Counts: {hand_counts}")
        diagnostic_lines.append(
            f"  Active Penalty: type={state.active_penalty_type}, count={state.active_penalty_count}"
        )

        # Invariant 1: Hand size validity (no negative sizes)
        for p, cards in state.hands.items():
            if len(cards) < 0:
                fail(f"Negative hand size detected for player {p}: {len(cards)}")

        # Invariant 2: Play pile validity
        if len(state.play_pile) < 1:
            fail("Play pile is empty after initialization")

        # Invariant 3: Card conservation
        total_cards = sum(len(cards) for cards in state.hands.values()) + len(state.market) + len(state.play_pile)
        if total_cards != TOTAL_DECK_SIZE:
            fail(f"Card conservation failed: total {total_cards} != {TOTAL_DECK_SIZE}")

        # Invariant 4: Card uniqueness
        seen_indices: Set[int] = set()
        seen_ids: Set[str] = set()

        def register_cards(cards: List[Any], loc_name: str) -> None:
            for card in cards:
                if card.card_index in seen_indices:
                    fail(f"Duplicate card index {card.card_index} ({card.id}) found in {loc_name}")
                if card.id in seen_ids:
                    fail(f"Duplicate card id {card.id} found in {loc_name}")
                seen_indices.add(card.card_index)
                seen_ids.add(card.id)

        for p, cards in state.hands.items():
            register_cards(cards, f"Player {p} hand")
        register_cards(state.market, "Market")
        register_cards(state.play_pile, "Play pile")

        if len(seen_indices) != TOTAL_DECK_SIZE:
            missing = set(range(TOTAL_DECK_SIZE)) - seen_indices
            fail(f"Missing physical card indices: {missing}")

        # Invariant 5: Current player validity
        if not (0 <= state.current_player < state.config.player_count):
            fail(
                f"Current player {state.current_player} out of range [0, {state.config.player_count - 1}]"
            )

        # Invariant 6: Current call validity
        if not state.current_call.is_ordinary:
            fail(f"Current call must be an ordinary shape, got {state.current_call}")

        # Invariant 7: Penalty validity
        if state.active_penalty_count > 0 and state.active_penalty_type is None:
            fail("Active penalty count is positive but active_penalty_type is None")
        if state.active_penalty_count == 0 and state.active_penalty_type is not None:
            fail(f"Active penalty type is {state.active_penalty_type} but count is 0")
        if state.active_penalty_count < 0:
            fail(f"Negative active penalty count: {state.active_penalty_count}")

        # Invariant 8: Terminal state validity
        if state.is_terminal:
            if state.winner is not None and not (0 <= state.winner < state.config.player_count):
                fail(f"Terminal winner {state.winner} out of range [0, {state.config.player_count - 1}]")
