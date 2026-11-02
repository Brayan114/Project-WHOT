"""Unit tests for Paper 2 Self-Play Wrapper and Rollout Buffer (P2-D1)."""

import pytest
import torch

from whot_ml.card import Shape
from whot_ml.observation import PlayerObservation
from whot_ml.ruleset import WHOTConfig

from experiments.paper2.envs.self_play_wrapper import SelfPlayEnvWrapper
from experiments.paper2.training.rollout_buffer import RolloutBuffer


def test_self_play_wrapper_reset():
    """Verify reset() returns a valid PlayerObservation matching current player."""
    env = SelfPlayEnvWrapper(num_players=4)
    obs = env.reset(seed=12345)

    assert isinstance(obs, PlayerObservation)
    assert obs.player_id == env.current_player
    assert len(obs.action_mask) == 76
    assert sum(obs.action_mask) > 0  # At least one legal move exists
    assert not env.is_terminal
    assert env.winner is None


def test_self_play_wrapper_full_episode():
    """Step through a complete self-play episode and assert terminal payoffs."""
    env = SelfPlayEnvWrapper(num_players=4)
    obs = env.reset(seed=54321)

    done = False
    step_count = 0
    max_steps = 1000

    last_reward = 0.0
    last_info = {}

    while not done and step_count < max_steps:
        # Greedily pick the first legal action index
        mask = obs.action_mask
        legal_actions = [idx for idx, val in enumerate(mask) if val == 1]
        assert len(legal_actions) > 0, f"No legal actions available at turn {step_count}"
        action = legal_actions[0]

        obs, reward, done, info = env.step(action)
        last_reward = reward
        last_info = info
        step_count += 1

    assert done, "Episode did not terminate within turn limit"
    assert "player_rewards" in last_info
    player_rewards = last_info["player_rewards"]
    assert len(player_rewards) == 4

    winner = env.winner
    if winner is not None:
        # Shedding victory
        assert player_rewards[winner] == 1.0
        for p in range(4):
            if p != winner:
                assert player_rewards[p] == -1.0
        acting_player = last_info["acting_player"]
        assert last_reward == (1.0 if acting_player == winner else -1.0)
    else:
        # Truncation
        assert last_info["truncated"]
        for p in range(4):
            assert player_rewards[p] == -1.0
        assert last_reward == -1.0


def test_rollout_buffer_shapes_and_gae():
    """Test RolloutBuffer capacity, storage, and GAE output dimensions."""
    buffer_size = 16
    obs_dim = 280
    action_dim = 76
    buffer = RolloutBuffer(buffer_size=buffer_size, obs_dim=obs_dim, action_dim=action_dim, num_players=4)

    # Populate buffer with dummy transitions
    for i in range(buffer_size):
        obs = torch.randn(obs_dim)
        action = i % action_dim
        log_prob = -1.5
        reward = 0.0
        value = 0.2 * i
        mask = torch.zeros(action_dim, dtype=torch.bool)
        mask[action] = True
        done = False
        player_id = i % 4

        buffer.add(
            obs=obs,
            action=action,
            log_prob=log_prob,
            reward=reward,
            value=value,
            mask=mask,
            done=done,
            player_id=player_id,
        )

    assert buffer.step_idx == buffer_size
    assert buffer.full

    # Compute GAE
    advantages, returns = buffer.compute_gae_and_returns(last_values=0.0, gamma=0.995, tau=0.95)

    assert advantages.shape == (buffer_size,)
    assert returns.shape == (buffer_size,)
    assert not torch.isnan(advantages).any()
    assert not torch.isnan(returns).any()


def test_rollout_buffer_multi_agent_terminal_rewards_propagation():
    """Verify that multi-agent terminal rewards propagate correctly to all participating seats."""
    buffer = RolloutBuffer(buffer_size=8, obs_dim=280, action_dim=76, num_players=4)

    # Simulate 8 sequential steps across 4 players:
    # Round 1: players 0, 1, 2, 3
    # Round 2: players 0, 1, 2, 3 (player 3 wins at step 7)
    for step in range(8):
        player_id = step % 4
        obs = torch.zeros(280)
        action = 0
        log_prob = -1.0
        reward = 0.0  # intermediate steps are 0.0
        value = 0.0
        mask = torch.ones(76, dtype=torch.bool)
        done = False

        buffer.add(
            obs=obs,
            action=action,
            log_prob=log_prob,
            reward=reward,
            value=value,
            mask=mask,
            done=done,
            player_id=player_id,
        )

    # Game terminates at step 7: player 3 wins (+1.0), players 0, 1, 2 lose (-1.0)
    terminal_rewards = {3: 1.0, 0: -1.0, 1: -1.0, 2: -1.0}
    buffer.finalize_episode(terminal_rewards)

    # 1. Verify that the terminal transitions of each player were correctly tagged
    # Player 3's last transition is step 7
    assert buffer.rewards[7].item() == 1.0
    assert buffer.dones[7].item() is True

    # Player 0's last transition is step 4
    assert buffer.rewards[4].item() == -1.0
    assert buffer.dones[4].item() is True

    # Player 1's last transition is step 5
    assert buffer.rewards[5].item() == -1.0
    assert buffer.dones[5].item() is True

    # Player 2's last transition is step 6
    assert buffer.rewards[6].item() == -1.0
    assert buffer.dones[6].item() is True

    # 2. Compute GAE per-player with zero critic values (V(s) = 0)
    # Target returns should equal discounted rewards:
    # For player 3:
    #   Step 7 (terminal): return = 1.0
    #   Step 3: return = gamma * 1.0 = 0.995 (since reward at step 3 was 0)
    # For player 0:
    #   Step 4 (terminal): return = -1.0
    #   Step 0: return = gamma * (-1.0) = -0.995
    gamma = 0.995
    advantages, returns = buffer.compute_gae_and_returns(last_values=0.0, gamma=gamma, tau=1.0, per_player=True)

    # Check winning player (seat 3)
    assert pytest.approx(returns[7].item(), abs=1e-4) == 1.0
    assert pytest.approx(returns[3].item(), abs=1e-4) == gamma * 1.0

    # Check losing player (seat 0)
    assert pytest.approx(returns[4].item(), abs=1e-4) == -1.0
    assert pytest.approx(returns[0].item(), abs=1e-4) == gamma * (-1.0)


def test_rollout_buffer_mini_batch_generator():
    """Verify get_batches() produces correctly dimensioned mini-batches."""
    buffer = RolloutBuffer(buffer_size=12, obs_dim=280, action_dim=76, num_players=4)
    for i in range(12):
        buffer.add(
            obs=torch.randn(280),
            action=i,
            log_prob=-0.5,
            reward=0.0,
            value=0.1,
            mask=torch.ones(76, dtype=torch.bool),
            done=False,
            player_id=i % 4,
        )
    buffer.compute_gae_and_returns(last_values=0.0)

    batches = list(buffer.get_batches(batch_size=4))
    assert len(batches) == 3

    for batch in batches:
        assert batch["observations"].shape == (4, 280)
        assert batch["actions"].shape == (4,)
        assert batch["advantages"].shape == (4,)
        assert batch["returns"].shape == (4,)
        assert batch["masks"].shape == (4, 76)
