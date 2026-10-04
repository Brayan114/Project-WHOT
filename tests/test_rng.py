"""Unit tests for RNGManager determinism and state restoration (P0-D4, P0-D5)."""

import pytest
from whot_ml.rng_manager import RNGManager


def test_rng_determinism():
    """Verify that identical seeds produce identical random sequences."""
    rng1 = RNGManager(seed=42)
    rng2 = RNGManager(seed=42)

    seq1 = list(range(54))
    seq2 = list(range(54))

    rng1.shuffle(seq1)
    rng2.shuffle(seq2)
    assert seq1 == seq2

    choices1 = [rng1.choice(seq1) for _ in range(10)]
    choices2 = [rng2.choice(seq2) for _ in range(10)]
    assert choices1 == choices2


def test_rng_state_capture_and_restoration():
    """Verify get_state and set_state allow exact replay of future draws."""
    rng = RNGManager(seed=12345)
    _ = [rng.randint(0, 100) for _ in range(5)]

    # Checkpoint
    saved_state = rng.get_state()

    # Generate forward path A
    future_a = [rng.randint(0, 1000) for _ in range(10)]

    # Restore and generate forward path B
    rng.set_state(saved_state)
    future_b = [rng.randint(0, 1000) for _ in range(10)]

    assert future_a == future_b
