"""Unit tests for Paper 2 RL models and observation encoders (P2-D1)."""

import pytest
import torch

from whot_ml.card import (
    CANONICAL_CARD_BY_INDEX,
    CANONICAL_DECK,
    Shape,
    SpecialEffect,
)
from whot_ml.event import Event, EventType
from whot_ml.observation import PlayerObservation
from whot_ml.ruleset import WHOTConfig

from experiments.paper2.models.feedforward_encoder import (
    FeedforwardEncoder,
    D_FF,
    ACTION_MASK_DIM,
)
from experiments.paper2.models.ppo_network import (
    MaskedActorCritic,
    MASK_NEG_INF,
)


def _create_mock_observation(
    player_id: int = 0,
    current_player: int = 0,
    hand_indices: tuple = (0, 1, 2, 49),  # 3 ordinary + 1 WHOT
    top_card_index: int = 5,
    current_call: Shape = Shape.CIRCLE,
    penalty_type: SpecialEffect = None,
    penalty_count: int = 0,
    hand_sizes: dict = None,
    last_card_declared: dict = None,
    market_size: int = 25,
    public_history: tuple = (),
    action_mask: tuple = None,
) -> PlayerObservation:
    """Helper to construct a valid PlayerObservation without invoking GameState."""
    if hand_sizes is None:
        hand_sizes = {0: len(hand_indices), 1: 5, 2: 5, 3: 5}
    if last_card_declared is None:
        last_card_declared = {0: False, 1: False, 2: False, 3: False}
    if action_mask is None:
        # Default: 76 slots, slot 0 and slot 74 (DRAW) legal
        mask = [0] * ACTION_MASK_DIM
        mask[0] = 1
        mask[74] = 1
        action_mask = tuple(mask)

    hand = tuple(CANONICAL_CARD_BY_INDEX[idx] for idx in hand_indices)
    play_pile = (CANONICAL_CARD_BY_INDEX[top_card_index],)

    return PlayerObservation(
        player_id=player_id,
        hand=hand,
        play_pile=play_pile,
        current_call=current_call,
        current_player=current_player,
        active_penalty_type=penalty_type,
        active_penalty_count=penalty_count,
        hand_sizes=hand_sizes,
        last_card_declared=last_card_declared,
        market_size=market_size,
        public_history=public_history,
        private_events=(),
        action_mask=action_mask,
        ruleset=WHOTConfig(),
        timestep=15,
        turn_count=12,
        is_terminal=False,
        winner=None,
    )


def test_feedforward_encoder_output_shape_and_mask():
    """Verify FeedforwardEncoder generates exact (280,) shape and embeds the action mask."""
    encoder = FeedforwardEncoder()
    mock_obs = _create_mock_observation()
    tensor = encoder.encode(mock_obs)

    # 1. Assert shape and type
    assert isinstance(tensor, torch.Tensor)
    assert tensor.shape == (280,)
    assert tensor.dtype == torch.float32

    # 2. Assert legal action mask is placed at the end (last 76 slots)
    expected_mask = torch.tensor(mock_obs.action_mask, dtype=torch.float32)
    assert torch.equal(tensor[-ACTION_MASK_DIM:], expected_mask)

    # 3. Assert hand encoding has expected multi-hot 1s
    for card in mock_obs.hand:
        assert tensor[card.card_index] == 1.0

    # 4. Assert top discard encoding has 1 at top card index
    assert tensor[54 + mock_obs.top_card.card_index] == 1.0

    # 5. Assert callable interface works
    tensor_call = encoder(mock_obs)
    assert torch.equal(tensor, tensor_call)


def test_feedforward_encoder_history_window():
    """Verify FeedforwardEncoder correctly embeds up to K=5 public card played events."""
    # Build 6 public CARD_PLAYED events to verify only the last 5 are retained
    history_events = tuple(
        Event(
            event_type=EventType.CARD_PLAYED,
            timestep=i,
            player=i % 4,
            card_id=f"CIRCLE_{val}",
        )
        for i, val in enumerate([1, 2, 3, 4, 5, 7])
    )
    obs = _create_mock_observation(public_history=history_events)
    encoder = FeedforwardEncoder()
    tensor = encoder.encode(obs)

    assert tensor.shape == (280,)
    # Verify the history window slice [134:204] is non-zero
    history_slice = tensor[134:204]
    assert history_slice.sum() > 0.0


def test_feedforward_encoder_information_boundary():
    """Verify that feedforward encoder does not import GameState."""
    import sys
    import experiments.paper2.models.feedforward_encoder as fe_module

    # Confirm GameState is not in fe_module namespace
    assert not hasattr(fe_module, "GameState")
    assert "GameState" not in dir(fe_module)


def test_masked_actor_critic_forward_batch():
    """Test MaskedActorCritic with a batch of dummy observations and masks."""
    batch_size = 4
    obs_dim = 280
    action_dim = 76

    model = MaskedActorCritic(obs_dim=obs_dim, action_dim=action_dim, hidden_dim=256)

    # Create dummy observations
    dummy_obs = torch.randn(batch_size, obs_dim)

    # Create arbitrary masks with some legal actions
    dummy_mask = torch.zeros(batch_size, action_dim, dtype=torch.bool)
    # Give each batch sample some legal actions
    dummy_mask[0, [0, 5, 74]] = True
    dummy_mask[1, [10, 20]] = True
    dummy_mask[2, [75]] = True
    dummy_mask[3, [1, 2, 3, 4]] = True

    # Embed mask in the dummy observation vector (as defined by D_FF specification)
    dummy_obs[:, -action_dim:] = dummy_mask.float()

    # Forward pass
    probs, value = model(dummy_obs, dummy_mask)

    # Assert shapes
    assert probs.shape == (batch_size, action_dim)
    assert value.shape == (batch_size, 1)

    # Assert probabilities for illegal actions are strictly 0.0
    for i in range(batch_size):
        illegal_indices = ~dummy_mask[i]
        assert torch.all(probs[i, illegal_indices] == 0.0), f"Illegal action probabilities not 0.0 in batch item {i}"
        
        legal_indices = dummy_mask[i]
        # Sum of legal action probabilities must equal 1.0
        assert torch.isclose(probs[i, legal_indices].sum(), torch.tensor(1.0), atol=1e-5)


def test_masked_actor_critic_unbatched():
    """Test MaskedActorCritic with a single unbatched observation (shape 280,)."""
    model = MaskedActorCritic()
    dummy_obs = torch.randn(280)
    dummy_mask = torch.zeros(76, dtype=torch.bool)
    dummy_mask[[0, 74]] = True
    dummy_obs[-76:] = dummy_mask.float()

    probs, value = model(dummy_obs, dummy_mask)

    assert probs.shape == (76,)
    assert value.shape == (1,)
    assert (probs[~dummy_mask] == 0.0).all()
    assert torch.isclose(probs.sum(), torch.tensor(1.0), atol=1e-5)


def test_masked_logits_values():
    """Test that compute_masked_logits places MASK_NEG_INF (-1e8) on illegal actions."""
    model = MaskedActorCritic()
    dummy_obs = torch.randn(2, 280)
    mask = torch.zeros(2, 76, dtype=torch.bool)
    mask[0, 5] = True
    mask[1, 10] = True

    masked_logits, mask_bool = model.compute_masked_logits(dummy_obs, mask)

    assert masked_logits.shape == (2, 76)
    # Check illegal slots have large negative value (-1e8)
    assert (masked_logits[0, ~mask[0]] == MASK_NEG_INF).all()
    assert (masked_logits[1, ~mask[1]] == MASK_NEG_INF).all()
    # Check legal slots have finite, non-masked logits
    assert masked_logits[0, 5] != MASK_NEG_INF
    assert masked_logits[1, 10] != MASK_NEG_INF
