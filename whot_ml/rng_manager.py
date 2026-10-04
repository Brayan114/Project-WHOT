"""Controlled, deterministic random number generation manager for WHOT-ML (P0-D4, P0-D5)."""

from __future__ import annotations

import random
from typing import Any, List, Optional, Sequence, Tuple, TypeVar

T = TypeVar("T")


class RNGManager:
    """Encapsulates all stochastic operations within the simulator.

    Guarantees that no uncontrolled system randomness enters the environment.
    Given the same initial seed, identical sequences of stochastic outcomes are produced.
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng = random.Random()
        self._initial_seed: Optional[int] = None
        self.reseed(seed)

    @property
    def initial_seed(self) -> Optional[int]:
        return self._initial_seed

    def reseed(self, seed: Optional[int]) -> None:
        """Seed or reseed the generator with a specific integer seed."""
        self._initial_seed = seed
        self._rng.seed(seed)

    def shuffle(self, seq: List[T]) -> None:
        """Deterministically shuffle an in-place list."""
        self._rng.shuffle(seq)

    def choice(self, seq: Sequence[T]) -> T:
        """Deterministically select a single element from a sequence."""
        if not seq:
            raise IndexError("Cannot choose from an empty sequence")
        return self._rng.choice(seq)

    def randint(self, a: int, b: int) -> int:
        """Return random integer in range [a, b], including both end points."""
        return self._rng.randint(a, b)

    def get_state(self) -> Tuple[Any, ...]:
        """Capture the internal RNG state for serialization and checkpointing."""
        return self._rng.getstate()

    def set_state(self, state: Tuple[Any, ...]) -> None:
        """Restore internal RNG state exactly."""
        self._rng.setstate(state)
