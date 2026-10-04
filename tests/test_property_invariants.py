"""Property-based invariant testing across hundreds of randomized game simulations (P0-D4 Section 40, 42.3)."""

import pytest
from whot_ml.action import index_to_action
from whot_ml.agents.random_agent import RandomLegalAgent
from whot_ml.card import TOTAL_DECK_SIZE
from whot_ml.environment import GameEnvironment
from whot_ml.invariants import InvariantValidator
from whot_ml.ruleset import WHOTConfig


def test_property_invariants_across_random_games():
    """Run 50 complete random games. After EVERY single action, assert:
      1. Exactly 54 physical cards exist.
      2. No physical card exists in multiple locations.
      3. No card has disappeared.
      4. Hand sizes are non-negative.
      5. Play pile has at least 1 card.
      6. Current player is in valid range.
      7. Active penalty state is internally consistent.
      8. Observation action mask matches legal_actions exactly.
    """
    for seed in range(50):
        env = GameEnvironment(config=WHOTConfig(debug_mode=True))
        env.reset(seed=1000 + seed)
        agents = {p: RandomLegalAgent(seed=p) for p in range(4)}

        step_count = 0
        while not env.is_terminal and step_count < 300:
            curr = env.current_player
            obs = env.observe(curr)

            # Property: action mask matches legal actions
            mask = obs.action_mask
            legal = obs.legal_actions
            assert len([a for a in legal]) == sum(mask)
            for act in legal:
                assert mask[act.action_id] == 1

            action = agents[curr].act(obs)
            step_result = env.step(action, acting_player=curr)
            step_count += 1

            # Property: Card conservation
            state = env.state
            total_cards = sum(len(h) for h in state.hands.values()) + len(state.market) + len(state.play_pile)
            assert total_cards == TOTAL_DECK_SIZE == 54

            # Property: Card uniqueness
            all_card_indices = [c.card_index for h in state.hands.values() for c in h]
            all_card_indices.extend(c.card_index for c in state.market)
            all_card_indices.extend(c.card_index for c in state.play_pile)
            assert len(all_card_indices) == 54
            assert set(all_card_indices) == set(range(54))

            # Property: Invariant validation check
            InvariantValidator.validate(state)


def test_property_different_player_counts_maintain_invariants():
    """Verify card conservation holds across 2, 3, 5, and 6 player games."""
    for n_players in (2, 3, 5, 6):
        env = GameEnvironment(config=WHOTConfig(player_count=n_players, starting_hand_size=4))
        env.reset(seed=2000 + n_players)
        agents = {p: RandomLegalAgent(seed=p) for p in range(n_players)}

        for _ in range(50):
            if env.is_terminal:
                break
            curr = env.current_player
            obs = env.observe(curr)
            action = agents[curr].act(obs)
            env.step(action, acting_player=curr)

            state = env.state
            total_cards = sum(len(h) for h in state.hands.values()) + len(state.market) + len(state.play_pile)
            assert total_cards == 54
