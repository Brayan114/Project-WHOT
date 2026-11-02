"""Latent Belief Linear/Logistic Probe for WHOT-ML Paper 2 (RQ3).

Extracts 256-dimensional latent representations from the frozen PPO policy network
during mid-game states (turns 20-60) and trains a probe to predict the presence
of unobserved cards in opponent hands. Evaluates macro AUROC against chance (0.50).
"""

from __future__ import annotations

import argparse
import math
import os
import random
import sys
from typing import Dict, List, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F

# Ensure repository root is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from whot_ml.action import index_to_action
from whot_ml.card import TOTAL_DECK_SIZE, CANONICAL_DECK
from whot_ml.environment import GameEnvironment
from whot_ml.ruleset import get_baseline_config

from experiments.paper2.envs.self_play_wrapper import SelfPlayEnvWrapper
from experiments.paper2.models.feedforward_encoder import FeedforwardEncoder
from experiments.paper2.models.ppo_network import MaskedActorCritic
from experiments.paper2.scripts.train_ppo import select_action


def compute_binary_auroc(y_true: torch.Tensor, y_pred: torch.Tensor) -> Optional[float]:
    """Compute exact Area Under the ROC Curve (AUROC) via Mann-Whitney statistic."""
    pos_mask = (y_true == 1)
    neg_mask = (y_true == 0)

    n_pos = pos_mask.sum().item()
    n_neg = neg_mask.sum().item()

    if n_pos == 0 or n_neg == 0:
        return None  # Only one class present

    pos_scores = y_pred[pos_mask]
    neg_scores = y_pred[neg_mask]

    # Vectorized pairwise comparison
    # pos_scores: (n_pos, 1), neg_scores: (1, n_neg)
    diff = pos_scores.unsqueeze(1) - neg_scores.unsqueeze(0)
    concordant = (diff > 0.0).float().sum().item()
    ties = (diff == 0.0).float().sum().item()

    auroc = (concordant + 0.5 * ties) / (float(n_pos) * float(n_neg))
    return float(auroc)


def collect_probe_dataset(
    network: MaskedActorCritic,
    encoder: FeedforwardEncoder,
    num_samples: int = 10000,
    seed: int = 90000,
    device: torch.device = torch.device("cpu"),
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Collect (activation, opponent_card_presence) pairs from mid-game states."""
    network.eval()
    activations_list: List[torch.Tensor] = []
    targets_list: List[torch.Tensor] = []

    collected = 0
    ep = 0

    print(f"[PROBE] Gathering {num_samples:,} mid-game observation-activation pairs...")

    while collected < num_samples:
        cfg = get_baseline_config()
        env = GameEnvironment(config=cfg)
        obs_dict = env.reset(seed=seed + ep)
        ep += 1

        terminated = False
        truncated = False

        while not (terminated or truncated) and collected < num_samples:
            curr_p = env.current_player
            obs = obs_dict[curr_p]
            turn = env.state.turn_count

            obs_tensor = encoder.encode(obs).to(device)
            mask_tensor = torch.tensor(obs.action_mask, dtype=torch.bool).to(device)

            with torch.no_grad():
                # Extract 256-dim representation from actor trunk
                z_t = network.actor_trunk(obs_tensor.unsqueeze(0)).squeeze(0).cpu()

            # Mid-game window: turn 20 to 60 (P2-D1 Section 2 RQ3)
            if 20 < turn <= 60:
                # Construct ground truth vector Y in {0, 1}^54
                # 1 if card is in ANY opponent's hand, 0 otherwise
                y_t = torch.zeros(TOTAL_DECK_SIZE, dtype=torch.float32)
                for opp in range(env.config.player_count):
                    if opp != curr_p:
                        for card in env.state.hands[opp]:
                            y_t[card.card_index] = 1.0

                activations_list.append(z_t)
                targets_list.append(y_t)
                collected += 1

                if collected % 2000 == 0:
                    print(f"  -> Collected {collected:,}/{num_samples:,} samples")

            # Advance game
            action_idx, _, _ = select_action(network, obs_tensor, mask_tensor, device, deterministic=False)
            action = index_to_action(action_idx)
            step_res = env.step(action)
            obs_dict[step_res.next_player] = step_res.observation
            terminated = step_res.terminated
            truncated = step_res.truncated

    X = torch.stack(activations_list, dim=0)  # (N, 256)
    Y = torch.stack(targets_list, dim=0)      # (N, 54)
    print(f"[PROBE] Dataset constructed: X shape {tuple(X.shape)}, Y shape {tuple(Y.shape)}")
    return X, Y


class LogisticProbe(nn.Module):
    """Linear probe with sigmoid outputs for multi-label card classification."""

    def __init__(self, in_features: int = 256, out_features: int = 54) -> None:
        super().__init__()
        self.linear = nn.Linear(in_features, out_features)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)


def train_and_evaluate_probe(
    X: torch.Tensor,
    Y: torch.Tensor,
    train_ratio: float = 0.80,
    epochs: int = 60,
    batch_size: int = 128,
    lr: float = 1e-2,
    weight_decay: float = 1e-4,
) -> Dict[str, Any]:
    """Train linear probe using BCE loss and compute macro test AUROC."""
    num_samples = X.shape[0]
    indices = torch.randperm(num_samples)
    split_idx = int(num_samples * train_ratio)

    train_idx = indices[:split_idx]
    test_idx = indices[split_idx:]

    X_train, Y_train = X[train_idx], Y[train_idx]
    X_test, Y_test = X[test_idx], Y[test_idx]

    probe = LogisticProbe(in_features=X.shape[1], out_features=Y.shape[1])
    optimizer = torch.optim.Adam(probe.parameters(), lr=lr, weight_decay=weight_decay)
    criterion = nn.BCEWithLogitsLoss()

    print(f"[PROBE] Training Logistic Probe on {len(X_train):,} samples for {epochs} epochs...")

    for epoch in range(epochs):
        perm = torch.randperm(len(X_train))
        epoch_loss = 0.0
        batches = 0

        for start in range(0, len(X_train), batch_size):
            b_idx = perm[start : start + batch_size]
            bx, by = X_train[b_idx], Y_train[b_idx]

            optimizer.zero_grad()
            logits = probe(bx)
            loss = criterion(logits, by)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            batches += 1

        if (epoch + 1) % 20 == 0 or epoch == epochs - 1:
            print(f"  Epoch {epoch+1:2d}/{epochs}: BCE Loss = {epoch_loss / max(1, batches):.4f}")

    # Evaluate on Test Set
    probe.eval()
    with torch.no_grad():
        test_logits = probe(X_test)
        test_probs = torch.sigmoid(test_logits)

    card_aurocs: List[float] = []
    for c in range(TOTAL_DECK_SIZE):
        auroc = compute_binary_auroc(Y_test[:, c], test_probs[:, c])
        if auroc is not None:
            card_aurocs.append(auroc)

    macro_auroc = sum(card_aurocs) / len(card_aurocs) if card_aurocs else 0.50
    min_auroc = min(card_aurocs) if card_aurocs else 0.50
    max_auroc = max(card_aurocs) if card_aurocs else 0.50

    print("\n" + "=" * 80)
    print("### RQ3 Latent Belief Probing Diagnostic Results")
    print("=" * 80)
    print(f"Number of Test Samples Evaluated : {len(X_test):,}")
    print(f"Number of Active Cards Probed   : {len(card_aurocs)}/54")
    print(f"Mean Macro AUROC                 : {macro_auroc:.4f}")
    print(f"Min Card AUROC                   : {min_auroc:.4f}")
    print(f"Max Card AUROC                   : {max_auroc:.4f}")
    print(f"Random Guessing Baseline         : 0.5000")
    print("-" * 80)

    if macro_auroc >= 0.70:
        conclusion = "STRONG SUPPORT (H3): Policy activations encode significant implicit belief of hidden cards."
    elif macro_auroc >= 0.58:
        conclusion = "MODERATE SIGNAL: Policy activations exceed chance, showing emerging card memory."
    else:
        conclusion = "CHANCE / NO SIGNAL: Policy activations do not separate hidden opponent cards (H3 refuted)."
    print(f"Conclusion: {conclusion}")
    print("=" * 80 + "\n")

    return {
        "macro_auroc": macro_auroc,
        "min_auroc": min_auroc,
        "max_auroc": max_auroc,
        "valid_cards_count": len(card_aurocs),
        "conclusion": conclusion,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Latent Belief Probe for WHOT-ML")
    parser.add_argument("--model-path", type=str, default="experiments/paper2/runs/pilot_10k/ppo_final_model.pt")
    parser.add_argument("--num-samples", type=int, default=10000)
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", type=str, default="cpu")

    args = parser.parse_args()

    device = torch.device(args.device)
    encoder = FeedforwardEncoder(num_players=4)
    network = MaskedActorCritic(obs_dim=280, action_dim=76, hidden_dim=256).to(device)

    if os.path.exists(args.model_path):
        network.load_state_dict(torch.load(args.model_path, map_location=device))
        print(f"[PROBE] Loaded model weights from {args.model_path}")
    else:
        print(f"[WARN] Model path {args.model_path} not found; using uninitialized weights.")

    X, Y = collect_probe_dataset(network, encoder, num_samples=args.num_samples, seed=args.seed, device=device)
    train_and_evaluate_probe(X, Y, epochs=args.epochs)


if __name__ == "__main__":
    main()
