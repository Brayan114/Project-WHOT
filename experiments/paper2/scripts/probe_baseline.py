"""Probe Baseline & Conditional AUROC Analysis for WHOT-ML.

Evaluates whether the latent belief probe (AUROC ~ 0.599) reflects genuine tracking
of unobserved cards versus trivial elimination of known cards (own hand and discard pile).

Computes:
1. Naive Elimination Baseline AUROC across all 54 cards.
2. Trained Probe AUROC across all 54 cards.
3. Naive Elimination Conditional AUROC (restricted strictly to unseen cards).
4. Trained Probe Conditional AUROC (restricted strictly to unseen cards).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
from typing import Dict, List, Optional, Tuple, Any

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

from experiments.paper2.models.feedforward_encoder import FeedforwardEncoder
from experiments.paper2.models.ppo_network import MaskedActorCritic
from experiments.paper2.scripts.train_ppo import select_action


def compute_binary_auroc(y_true: torch.Tensor, y_pred: torch.Tensor) -> Optional[float]:
    """Compute exact Area Under the ROC Curve (AUROC) via Mann-Whitney statistic."""
    pos_mask = (y_true == 1)
    neg_mask = (y_true == 0)

    n_pos = int(pos_mask.sum().item())
    n_neg = int(neg_mask.sum().item())

    if n_pos == 0 or n_neg == 0:
        return None

    pos_scores = y_pred[pos_mask]
    neg_scores = y_pred[neg_mask]

    diff = pos_scores.unsqueeze(1) - neg_scores.unsqueeze(0)
    concordant = float((diff > 0.0).float().sum().item())
    ties = float((diff == 0.0).float().sum().item())

    auroc = (concordant + 0.5 * ties) / (float(n_pos) * float(n_neg))
    return float(auroc)


class LogisticProbe(nn.Module):
    """Linear probe with sigmoid outputs for multi-label card classification."""

    def __init__(self, in_features: int = 256, out_features: int = 54) -> None:
        super().__init__()
        self.linear = nn.Linear(in_features, out_features)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)


def collect_probe_dataset_with_seen(
    network: MaskedActorCritic,
    encoder: FeedforwardEncoder,
    num_samples: int = 10000,
    seed: int = 90000,
    device: torch.device = torch.device("cpu"),
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Collect (activations, ground_truth, seen_mask) tuples from mid-game states."""
    network.eval()
    activations_list: List[torch.Tensor] = []
    targets_list: List[torch.Tensor] = []
    seen_list: List[torch.Tensor] = []

    collected = 0
    ep = 0

    print(f"[PROBE-BASELINE] Gathering {num_samples:,} mid-game observation-activation pairs...")

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
                z_t = network.actor_trunk(obs_tensor.unsqueeze(0)).squeeze(0).cpu()

            # Mid-game window: turn 20 to 60
            if 20 < turn <= 60:
                y_t = torch.zeros(TOTAL_DECK_SIZE, dtype=torch.float32)
                for opp in range(env.config.player_count):
                    if opp != curr_p:
                        for card in env.state.hands[opp]:
                            y_t[card.card_index] = 1.0

                seen_t = torch.zeros(TOTAL_DECK_SIZE, dtype=torch.bool)
                # Cards currently in acting player's private hand
                for card in env.state.hands[curr_p]:
                    seen_t[card.card_index] = True
                # Cards in the public discard pile
                for card in env.state.play_pile:
                    seen_t[card.card_index] = True

                activations_list.append(z_t)
                targets_list.append(y_t)
                seen_list.append(seen_t)
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

    X = torch.stack(activations_list, dim=0)    # (N, 256)
    Y = torch.stack(targets_list, dim=0)        # (N, 54)
    Seen = torch.stack(seen_list, dim=0)        # (N, 54) bool
    print(f"[PROBE-BASELINE] Dataset ready: X={tuple(X.shape)}, Y={tuple(Y.shape)}, Seen={tuple(Seen.shape)}")
    return X, Y, Seen


def evaluate_probe_and_baseline(
    X: torch.Tensor,
    Y: torch.Tensor,
    Seen: torch.Tensor,
    train_ratio: float = 0.80,
    epochs: int = 60,
    batch_size: int = 128,
    lr: float = 1e-2,
    weight_decay: float = 1e-4,
) -> Dict[str, Any]:
    """Train probe and compute both overall and conditional AUROCs."""
    num_samples = X.shape[0]
    indices = torch.randperm(num_samples)
    split_idx = int(num_samples * train_ratio)

    train_idx = indices[:split_idx]
    test_idx = indices[split_idx:]

    X_train, Y_train = X[train_idx], Y[train_idx]
    X_test, Y_test = X[test_idx], Y[test_idx]
    Seen_test = Seen[test_idx]
    Unseen_test = ~Seen_test

    # 1. Train Logistic Probe
    probe = LogisticProbe(in_features=X.shape[1], out_features=Y.shape[1])
    optimizer = torch.optim.Adam(probe.parameters(), lr=lr, weight_decay=weight_decay)
    criterion = nn.BCEWithLogitsLoss()

    print(f"\n[PROBE-BASELINE] Training probe on {len(X_train):,} samples for {epochs} epochs...")
    for epoch in range(epochs):
        perm = torch.randperm(len(X_train))
        for start in range(0, len(X_train), batch_size):
            b_idx = perm[start : start + batch_size]
            bx, by = X_train[b_idx], Y_train[b_idx]
            optimizer.zero_grad()
            logits = probe(bx)
            loss = criterion(logits, by)
            loss.backward()
            optimizer.step()

    probe.eval()
    with torch.no_grad():
        test_logits = probe(X_test)
        probe_probs = torch.sigmoid(test_logits)

    # 2. Naive Elimination Predictions
    # Predict 1.0 if unseen, 0.0 if seen
    naive_probs = Unseen_test.float()

    # 3. Compute Metrics Across All Cards (Full Set)
    probe_full_aurocs: List[float] = []
    naive_full_aurocs: List[float] = []

    for c in range(TOTAL_DECK_SIZE):
        p_auc = compute_binary_auroc(Y_test[:, c], probe_probs[:, c])
        n_auc = compute_binary_auroc(Y_test[:, c], naive_probs[:, c])
        if p_auc is not None:
            probe_full_aurocs.append(p_auc)
        if n_auc is not None:
            naive_full_aurocs.append(n_auc)

    mean_probe_full = sum(probe_full_aurocs) / len(probe_full_aurocs)
    mean_naive_full = sum(naive_full_aurocs) / len(naive_full_aurocs)

    # 4. Compute Conditional Metrics (Restricted Strictly to Unseen Cards)
    probe_cond_aurocs: List[float] = []
    naive_cond_aurocs: List[float] = []

    for c in range(TOTAL_DECK_SIZE):
        unseen_mask = Unseen_test[:, c]
        if unseen_mask.sum().item() > 0:
            y_unseen = Y_test[unseen_mask, c]
            p_unseen = probe_probs[unseen_mask, c]
            n_unseen = naive_probs[unseen_mask, c]

            p_auc = compute_binary_auroc(y_unseen, p_unseen)
            n_auc = compute_binary_auroc(y_unseen, n_unseen)

            if p_auc is not None:
                probe_cond_aurocs.append(p_auc)
            if n_auc is not None:
                naive_cond_aurocs.append(n_auc)

    mean_probe_cond = sum(probe_cond_aurocs) / len(probe_cond_aurocs) if probe_cond_aurocs else 0.50
    mean_naive_cond = sum(naive_cond_aurocs) / len(naive_cond_aurocs) if naive_cond_aurocs else 0.50

    results = {
        "num_test_samples": len(X_test),
        "mean_probe_full_auroc": mean_probe_full,
        "mean_naive_full_auroc": mean_naive_full,
        "mean_probe_conditional_auroc": mean_probe_cond,
        "mean_naive_conditional_auroc": mean_naive_cond,
        "probe_full_min": min(probe_full_aurocs),
        "probe_full_max": max(probe_full_aurocs),
        "probe_cond_min": min(probe_cond_aurocs) if probe_cond_aurocs else 0.50,
        "probe_cond_max": max(probe_cond_aurocs) if probe_cond_aurocs else 0.50,
    }

    print("\n" + "=" * 80)
    print("### PROBE BASELINE & CONDITIONAL AUROC RESULTS")
    print("=" * 80)
    print(f"Test Samples Evaluated               : {len(X_test):,}")
    print(f"Overall Probe Macro AUROC (Full)     : {mean_probe_full:.4f}")
    print(f"Overall Naive Elimination AUROC (Full): {mean_naive_full:.4f}")
    print(f"Conditional Probe AUROC (Unseen Only): {mean_probe_cond:.4f}")
    print(f"Conditional Naive AUROC (Unseen Only): {mean_naive_cond:.4f}")
    print("-" * 80)
    if mean_probe_cond > 0.52:
        print("Verdict: The network demonstrates GENUINE latent tracking of hidden opponent cards beyond trivial elimination.")
    else:
        print("Verdict: The probe's advantage is primarily driven by trivial elimination (hand + discard knowledge).")
    print("=" * 80 + "\n")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe Baseline Evaluation")
    parser.add_argument(
        "--model-path",
        type=str,
        default="experiments/paper2/runs/kaggle_production_10m/whot_ppo_10m/ppo_final_model_10m.pt",
    )
    parser.add_argument("--num-samples", type=int, default=10000)
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-json", type=str, default="experiments/paper2/runs/probe_baseline_results.json")

    args = parser.parse_args()

    device = torch.device("cpu")
    encoder = FeedforwardEncoder(num_players=4)
    network = MaskedActorCritic(obs_dim=280, action_dim=76, hidden_dim=256).to(device)

    if os.path.exists(args.model_path):
        network.load_state_dict(torch.load(args.model_path, map_location=device))
        print(f"[PROBE-BASELINE] Loaded model from {args.model_path}")
    else:
        print(f"[ERROR] Model path {args.model_path} not found!")
        sys.exit(1)

    X, Y, Seen = collect_probe_dataset_with_seen(
        network, encoder, num_samples=args.num_samples, seed=args.seed, device=device
    )
    res = evaluate_probe_and_baseline(X, Y, Seen, epochs=args.epochs)

    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print(f"Saved results to {args.output_json}")


if __name__ == "__main__":
    main()
