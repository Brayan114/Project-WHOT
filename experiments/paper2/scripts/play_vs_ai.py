#!/usr/bin/env python3
"""Interactive CLI script: Human vs. Trained PPO Agents in WHOT-ML.

Allows the user (Brayan) to play a full 4-player game of Nigerian WHOT against
trained deep reinforcement learning agents (Masked PPO).

Usage:
    python experiments/paper2/scripts/play_vs_ai.py
    python experiments/paper2/scripts/play_vs_ai.py --model-path experiments/paper2/runs/kaggle_production_10m/whot_ppo_10m/ppo_final_model_10m.pt
    python experiments/paper2/scripts/play_vs_ai.py --model-path experiments/paper2/runs/pilot_10k/ppo_final_model.pt
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import List, Optional

# Ensure repository root is in sys.path for direct script execution
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import torch

from whot_ml.action import Action, ActionType, index_to_action
from whot_ml.card import (
    CANONICAL_CARD_BY_INDEX,
    Card,
    Shape,
    SpecialEffect,
)
from whot_ml.environment import GameEnvironment
from whot_ml.observation import PlayerObservation
from whot_ml.ruleset import StarterPolicy, WHOTConfig
from experiments.paper2.models.feedforward_encoder import FeedforwardEncoder
from experiments.paper2.models.ppo_network import MaskedActorCritic


def format_card(card: Card) -> str:
    """Format a Card object into a human-readable title-cased string."""
    if card.is_whot:
        return f"WHOT {card.value}"
    effect_str = ""
    if card.default_effect:
        name = card.default_effect.name.replace("_", " ").title()
        effect_str = f" ({name})"
    return f"{card.shape.name.title()} {card.value}{effect_str}"


def format_action(action: Action) -> str:
    """Format an Action object into an intuitive, readable English phrase."""
    if action.action_type == ActionType.PLAY:
        card = CANONICAL_CARD_BY_INDEX[action.action_id]
        return f"Play {format_card(card)}"
    elif action.action_type == ActionType.PLAY_WHOT:
        shape_name = action.selected_shape.name.title() if action.selected_shape else "?"
        return f"Play WHOT 20 -> Call {shape_name}"
    elif action.action_type == ActionType.DRAW:
        return "Draw card from market"
    elif action.action_type == ActionType.DECLARE_LAST:
        return "Declare LAST CARD!"
    return str(action)


def print_banner() -> None:
    """Print the welcoming header for the game."""
    print("=" * 70)
    print("     WHOT-ML: Human (Brayan) vs. Deep Reinforcement Learning (PPO)")
    print("     Nigerian WHOT • 4-Player Multi-Agent POMDP Environment")
    print("=" * 70)
    print("You are Player 0. The AI agents control Players 1, 2, and 3.")
    print("Type the number corresponding to your chosen action, or 'q' to quit.")
    print("=" * 70)
    print()


def display_game_state(obs: PlayerObservation, timestep: int) -> None:
    """Display the visible game state and human hand cleanly."""
    top_card_str = format_card(obs.top_card)
    call_str = obs.current_call.name.title() if obs.current_call else "None"

    # Pending penalty details
    if obs.active_penalty_count > 0:
        penalty_type = obs.active_penalty_type.name.replace("_", " ").title() if obs.active_penalty_type else "Penalty"
        penalty_str = f"+{obs.active_penalty_count} cards pending from {penalty_type}"
    else:
        penalty_str = "None"

    # Hand sizes summary
    sizes = []
    for pid in range(4):
        pname = "You" if pid == 0 else f"AI {pid}"
        decl = " [LAST CARD!]" if obs.last_card_declared.get(pid, False) else ""
        sizes.append(f"{pname}: {obs.hand_sizes.get(pid, '?')}{decl}")
    hand_sizes_str = "  |  ".join(sizes)

    print("-" * 70)
    print(f"[Turn {timestep}] Current Player: YOU (Player 0)")
    print("-" * 70)
    print(f"  Top Discard    : {top_card_str}")
    print(f"  Active Call    : {call_str}")
    print(f"  Active Penalty : {penalty_str}")
    print(f"  Market Size    : {obs.market_size} cards remaining")
    print(f"  Player Hands   : {hand_sizes_str}")
    print("-" * 70)

    # Human hand display
    print(f"Your Hand ({len(obs.hand)} cards):")
    for idx, card in enumerate(obs.hand):
        print(f"   [{idx}] {format_card(card)}")
    print()


def prompt_human_action(legal_actions: List[Action]) -> Action:
    """Prompt the human player to select one of the legal actions."""
    print("Legal Actions:")
    for idx, act in enumerate(legal_actions, 1):
        print(f"  [{idx}] {format_action(act)}")
    print()

    while True:
        try:
            choice = input(f"Enter action number [1-{len(legal_actions)}] (or 'q' to quit): ").strip()
            if choice.lower() in ("q", "quit", "exit"):
                print("\nGame aborted by user. Exiting...")
                sys.exit(0)
            act_num = int(choice)
            if 1 <= act_num <= len(legal_actions):
                selected = legal_actions[act_num - 1]
                print(f"\n>> You chose: {format_action(selected)}\n")
                return selected
            else:
                print(f"Invalid number. Please enter an integer between 1 and {len(legal_actions)}.")
        except ValueError:
            print(f"Invalid input. Please enter a number between 1 and {len(legal_actions)}.")


def play_game(
    model_path: str,
    seed: Optional[int] = None,
    delay: float = 0.4,
    device: str = "cpu",
    starter_policy: StarterPolicy = StarterPolicy.FIXED_PLAYER_0,
) -> None:
    """Run an interactive match between Human (Player 0) and AI (Players 1-3)."""
    # 1. Load PPO Model
    if not os.path.exists(model_path):
        print(f"Error: Model checkpoint not found at '{model_path}'")
        sys.exit(1)

    print(f"Loading trained PPO model from: {model_path} ...")
    model = MaskedActorCritic(obs_dim=280, action_dim=76)
    ckpt = torch.load(model_path, map_location=device)
    state_dict = ckpt["model_state_dict"] if isinstance(ckpt, dict) and "model_state_dict" in ckpt else ckpt
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    encoder = FeedforwardEncoder(num_players=4)

    # 2. Setup Environment
    config = WHOTConfig(
        player_count=4,
        starter_policy=starter_policy,
    )
    env = GameEnvironment(config=config)
    env.reset(seed=seed)

    print_banner()
    timestep = 0

    # 3. Main Game Loop
    while not env.is_terminal:
        timestep += 1
        current = env.current_player

        if current == 0:
            # Human's Turn
            obs = env.observe(0)
            display_game_state(obs, timestep)
            legal_actions = env.legal_actions(0)
            if not legal_actions:
                print("No legal actions available. Passing...")
                break
            action = prompt_human_action(legal_actions)
            env.step(action)
        else:
            # AI's Turn
            obs = env.observe(current)
            feature_vec = encoder.encode(obs).unsqueeze(0).to(device)
            mask_vec = torch.tensor(env.action_mask(current), dtype=torch.bool).unsqueeze(0).to(device)

            with torch.no_grad():
                action_probs, _ = model(feature_vec, mask_vec)
                chosen_id = torch.argmax(action_probs, dim=-1).item()

            action = index_to_action(chosen_id)
            decl_suffix = " (Declared LAST CARD!)" if obs.last_card_declared.get(current, False) else ""
            print(f"[Turn {timestep:3d}] AI {current} ({len(obs.hand)} cards{decl_suffix}) -> {format_action(action)}")

            if delay > 0:
                time.sleep(delay)

            env.step(action)

    # 4. Game Over Screen
    print("\n" + "=" * 70)
    print("                            GAME OVER")
    print("=" * 70)

    winner = env.winner
    if winner == 0:
        print("  🏆 VICTORY! Congratulations Brayan, you defeated the AI agents! 🏆")
    elif winner is not None:
        print(f"  💀 DEFEAT! AI Player {winner} won the game!")
    else:
        print("  🤝 DRAW / TRUNCATION! The game reached maximum turns without a shed.")

    print("-" * 70)
    print(f"Total Turns Played: {timestep}")
    print("Final Hand Sizes:")
    final_obs = env.observe(0)
    for pid in range(4):
        pname = "You (Player 0)" if pid == 0 else f"AI {pid}"
        win_str = " [WINNER]" if pid == winner else ""
        print(f"  - {pname:<16}: {final_obs.hand_sizes.get(pid, 0)} cards{win_str}")
    print("=" * 70)
    print()


def main() -> None:
    default_10m = "experiments/paper2/runs/kaggle_production_10m/whot_ppo_10m/ppo_final_model_10m.pt"
    default_pilot = "experiments/paper2/runs/pilot_10k/ppo_final_model.pt"
    default_path = default_10m if os.path.exists(default_10m) else default_pilot

    parser = argparse.ArgumentParser(description="Play Nigerian WHOT against trained PPO agents.")
    parser.add_argument(
        "--model-path",
        type=str,
        default=default_path,
        help="Path to trained PPO model checkpoint (.pt)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for repeatable initial deals (optional)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.3,
        help="Seconds delay after each AI move for readability (default: 0.3s)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Inference device: 'cpu' or 'cuda' (default: cpu)",
    )
    parser.add_argument(
        "--random-starter",
        action="store_true",
        help="Randomize who starts (default is Human starts first)",
    )

    args = parser.parse_args()
    starter = StarterPolicy.RANDOM if args.random_starter else StarterPolicy.FIXED_PLAYER_0

    play_game(
        model_path=args.model_path,
        seed=args.seed,
        delay=args.delay,
        device=args.device,
        starter_policy=starter,
    )


if __name__ == "__main__":
    main()
