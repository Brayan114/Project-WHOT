# WHOT-ML — Paper 2: Reinforcement Learning & Self-Play Integration

This directory houses the reinforcement learning baselines, training pipelines, self-play matchmaking, and evaluation suites for WHOT-ML, following the formal specification in `docs/P2-D1 — Paper 2 Experimental Specification v0.1.md`.

## Immutable Rule
The underlying simulator `whot_ml/` is strictly frozen. All RL wrappers, neural network architectures, trajectory buffers, self-play managers, and evaluation probes reside strictly within `experiments/paper2/`.

## Directory Structure
- `configs/`: Hyperparameter configurations for PPO (and optional DQN) training runs, observation feature sets, and self-play matchmaking.
- `models/`: PyTorch neural network definitions:
  - Observation feature encoders (vector and recurrent GRU).
  - Actor-critic heads with action masking (`m_t \in \{0, 1\}^{76}`).
- `scripts/`: Training runners and parallel rollout workers:
  - `train_ppo.py`: Action-masked PPO with vectorized environment workers.
  - `evaluate_checkpoints.py`: Periodic evaluation against baseline agents.
- `evaluation/`: Tournament benchmarking, belief probing, and strategic diagnostic suites:
  - Asymmetric tournament evaluation (1 RL vs. 3 RandomLegal / 3 RuleBased).
  - Symmetric 4-player RL self-play stall assessment (truncation rate vs. RuleBased 41.4%).
  - Hidden-hand linear and non-linear probing (AUROC on opponent card prediction).
- `runs/`: Checkpoint weights, tensorboard event logs, and evaluation metrics.
