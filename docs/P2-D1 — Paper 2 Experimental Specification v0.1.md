# WHOT-ML — P2-D1: Paper 2 Experimental Specification v0.1

## Document Metadata & Status

- **Phase:** Phase 2 — Reinforcement Learning, Self-Play & Belief Representation
- **Document ID:** P2-D1 — Paper 2 Experimental Specification
- **Version:** 0.1
- **Target Manuscript:** *“Reinforcement Learning in WHOT: Self-Play Dynamics, Defensive Stall Emergence, and Latent Belief Representation”* (WHOT-ML Paper 2)
- **Baseline Simulator:** `WHOT-NG-v1.0` (Git Commit `7c1a2dc`, strictly frozen)
- **Baseline Environment:** `WHOT-NG-v1`
- **Validation Status:** 109/109 regression tests passing (100% pass rate)
- **Document Status:** FORMAL PLANNED EXPERIMENTAL SPECIFICATION (Pre-implementation freeze)

---

# 1. Executive Summary & Core Principles

This specification formalizes the empirical methodology, algorithmic framework, tensor encoding architectures, diagnostic batteries, probing mechanics, and evaluation protocols for Paper 2 of the WHOT-ML research program.

Paper 1 established:
1. An open-source, deterministic reference environment (`WHOT-NG-v1.0`) frozen at commit `7c1a2dc`.
2. Strict mathematical formalization of WHOT as a multi-agent POMDP with 0.0% measured information leakage.
3. Bitwise reproducibility across state rollouts and checkpoints.
4. Two reference baseline policies: `RandomLegalAgent` (uniform stochastic) and `RuleBasedAgent` (greedy heuristic with domain logic).
5. A critical empirical baseline finding: 4-player heuristic self-play (`BBBB`) collapses into an emergent defensive stall, resulting in a **43.6% truncation rate** at the 1,000-turn limit due to retaliatory penalty loops and continuous discard market recycling.

Paper 2 investigates whether model-free reinforcement learning algorithms can master WHOT from tabula rasa self-play, overcome or succumb to the emergent heuristic stall, develop internal representations of unobserved world states (hidden opponent hands), and generalize against divergent opponent styles.

### 1.1 Non-Negotiable Simulator Freeze Invariant
The simulator `WHOT-NG-v1.0` is an immutable scientific instrument:
1. Files under `whot_ml/` **MUST NOT** be modified, refactored, patched, or adapted.
2. The 54-card deck ontology, the 76-slot action space, observation generation invariants, effect resolution pipelines, and game termination mechanics are frozen.
3. All RL training scripts, neural network architectures, vector observation encoders, trajectory buffers, self-play matchmaking managers, and probe evaluators must reside strictly outside `whot_ml/` in `experiments/paper2/`.
4. If an RL agent fails to converge, displays degenerate behavior, or stalls, this constitutes an empirical finding rather than a license to adjust simulator mechanics or alter reward thresholds to ease learning.

---

# 2. Research Questions & Formal Hypotheses

Paper 2 is structured around four foundational research questions:

## RQ1: Can model-free RL agents (PPO, optionally DQN) learn competent WHOT play from self-play in WHOT-NG-v1?
- **Hypothesis (H1):** Tabula rasa Proximal Policy Optimization (PPO) using action-masked policies in symmetric self-play will achieve super-random competence, converging to a policy that significantly outperforms `RandomLegalAgent` (>70% win rate in asymmetric 4-player evaluation) without reward shaping beyond sparse terminal game outcomes and hand-penalty signals.
- **Independent Variables:**
  - RL Algorithm: Masked PPO (Primary), Action-Masked DQN (Secondary ablation).
  - Observation Architecture: Feedforward vector encoding vs. Recurrent (GRU) sequence encoding.
  - Compute Scale: Number of environment frames (1M, 2.5M, 5M, 10M steps).
- **Dependent Variables:**
  - Win rate against `RandomLegalAgent` in asymmetric tournament (1 RL vs. 3 Random).
  - Policy entropy $H(\pi_\theta)$.
  - Value function explained variance ($R^2_{\text{val}}$).
  - Illegal action submission rate (0.0% target via mask verification).
- **Controlled Variables:**
  - 4-player standard ruleset (`WHOTConfig` baseline: 54 cards, Pick-2/Pick-3 stacking enabled, Last Card declaration required).
  - Turn limit: 1,000 turns.
  - Random seed protocol: 5 independent training seeds with disjoint evaluation seed sets.
- **Compute Budget:** 5 seeds $\times$ 10M frames $\approx$ 15 GPU hours on NVIDIA T4/P100.
- **Success Criteria:**
  - *Support:* Trained policy achieves $\ge 60.0\%$ win rate (Wilson 95% CI lower bound $> 55.0\%$) against 3 `RandomLegalAgent` opponents across 1,000 test games.
  - *Refutation:* Policy fails to exceed fair-share 25% ($p > 0.05$) or policy entropy collapses to a uniform random distribution or single-action deadlock.

## RQ2: Does self-play RL escape the emergent defensive stall observed in RuleBased self-play (43.6% truncation rate), or does it also get stuck? If it escapes, what strategy emerges?
- **Hypothesis (H2):** Symmetric self-play RL will escape the retaliatory penalty stall observed in heuristic agents, reducing the 4-player self-play truncation rate from 43.6% to <10.0%. The emerging policy will favor card-dumping and tempo-preserving moves over aggressive, uncalculated penalty card deployment that triggers market recycling.
- **Independent Variables:**
  - Policy origin: `RuleBasedAgent` vs. Trained Self-Play RL Checkpoints across training epochs ($t \in \{1\text{M}, 2.5\text{M}, 5\text{M}, 10\text{M}\}$).
  - Reward structure: Pure terminal win/loss ($\pm 1$) vs. Terminal win/loss augmented with hand-difference minimization ($\Delta \text{Hand}$).
- **Dependent Variables:**
  - Symmetric 4-player truncation rate (% games reaching $t=1,000$).
  - Mean game length (turns to termination).
  - Market reshuffle frequency per episode.
  - Strategic composition of play: Ratio of special action cards played (Pick-2, Pick-3, General Market) to ordinary number-matching plays.
  - Hand size variance across players over episode progression.
- **Controlled Variables:**
  - Standard 4-player environment, identical initial deal seeds (matched seeds 10000–10999).
- **Compute Budget:** 1,000 evaluation episodes per checkpoint $\times$ 5 checkpoints $\times$ 5 seeds = 25,000 evaluation games (approx 4 CPU hours).
- **Success Criteria:**
  - *Support:* 4-player symmetric RL self-play achieves a truncation rate $\le 10.0\%$ (statistically significantly lower than heuristic self-play at $p < 10^{-10}$ via Fisher's exact test) while maintaining legal terminal victory.
  - *Refutation:* RL self-play exhibits $\ge 35.0\%$ truncation rate, or reduces truncations purely by cycling into rapid draw-exhaustion terminations without strategic card depletion.

## RQ3: Do learned policies develop internal representations of hidden information (i.e., implicit belief state about opponent hands)?
- **Hypothesis (H3):** A linear or shallow non-linear probe trained on the hidden activations of a recurrent (GRU) RL agent will predict the presence of specific cards in opponent hands with an accuracy and AUROC significantly superior to both a random baseline and a feedforward network baseline that only sees immediate public history.
- **Independent Variables:**
  - Encoder Architecture: Feedforward (window $K=5$) vs. Recurrent GRU (full public history).
  - Layer depth probed: Latent representations at Layer 1, Layer 2, and GRU hidden state $h_t$.
  - Game phase: Opening ($t \le 20$), Mid-game ($20 < t \le 60$), Late-game ($t > 60$).
- **Dependent Variables:**
  - Opponent Card Classification AUROC (multi-label binary classification across 54 cards).
  - Macro F1-score of opponent hand presence prediction.
  - Linear probe mutual information estimate $\hat{I}(Z; H_{-i})$.
- **Controlled Variables:**
  - Probe architecture (single linear layer with sigmoid output, frozen agent backbone).
  - Training dataset: 50,000 mid-game observation-activation pairs generated under frozen evaluation rollouts.
- **Compute Budget:** Probe extraction and training: approx 2 GPU hours.
- **Success Criteria:**
  - *Support:* GRU hidden state probe achieves macro AUROC $\ge 0.70$ on unseen opponent card prediction in mid-to-late game states, outperforming feedforward probe by $\ge 0.10$ AUROC.
  - *Refutation:* Probe performance on recurrent activations does not significantly exceed the feedforward baseline or trivial marginal card prevalence baselines (AUROC $\le 0.55$).

## RQ4: How do learned policies compare to RandomLegalAgent and RuleBasedAgent baselines, and do they generalize to unseen opponent policies?
- **Hypothesis (H4):** Self-play trained PPO policies will dominate `RuleBasedAgent` in head-to-head play (>60% win rate in 2-player and >40% in 4-player asymmetric BRRR), but will exhibit exploitability or performance degradation when facing out-of-distribution heuristic styles unless exposed to population-based training.
- **Independent Variables:**
  - Training regime: Pure symmetric self-play vs. Population-based training (FSP / league training).
  - Test Opponent Population:
    - 4-Player Asymmetric: 1 RL vs. 3 Random (`RRR`), 1 RL vs. 3 RuleBased (`BBB`).
    - 4-Player Mixed: 1 RL + 1 RuleBased + 2 Random (`RBR`).
    - 2-Player Heads-Up: RL vs. RuleBased, RL vs. Random.
- **Dependent Variables:**
  - Win rate (Wilson score 95% CI).
  - Average finishing rank (1.0 to 4.0).
  - Mean turns to win vs. mean turns to loss.
- **Controlled Variables:**
  - Seat rotation protocol (cyclic permutation across all 4 seating positions to eliminate seat bias).
  - 1,000 test games per configuration across fixed evaluation seeds (60000–60999).
- **Compute Budget:** approx 6 CPU hours for full cross-matchup tournament matrix.
- **Success Criteria:**
  - *Support:* RL policy achieves $\ge 60.0\%$ win rate against `RuleBasedAgent` in 2-player heads-up and $\ge 35.0\%$ in 4-player 1v3 RuleBased matchup (where fair share is 25.0%).
  - *Refutation:* RL policy fails to achieve statistical parity (<25.0% win rate) against `RuleBasedAgent` in 4-player play, indicating that pure self-play overfits to idiosyncratic self-play conventions.

---

# 3. Technical Specifications

## A. Algorithm Specification

### Primary Algorithm: Masked Proximal Policy Optimization (PPO)
PPO is selected as the primary algorithmic workhorse due to its numerical stability in extensive-form multi-agent games, natural compatibility with actor-critic value estimation, and proven track record in complex imperfect-information benchmarks (e.g., OpenAI Five, Hanabi).

#### Core Hyperparameters:
| Hyperparameter | Value | Rationale & Benchmark Reference |
| :--- | :--- | :--- |
| **Policy Formulation** | Actor-Critic (Separate trunks) | Separate backbones eliminate policy-value gradient interference (Yu et al., MAPPO, 2022) |
| **Actor Optimizer** | Adam ($\beta_1 = 0.9, \beta_2 = 0.999, \epsilon = 10^{-7}$) | Standard stable momentum configuration |
| **Critic Optimizer** | Adam ($\beta_1 = 0.9, \beta_2 = 0.999, \epsilon = 10^{-7}$) | Standard configuration |
| **Actor Learning Rate** | $3.0 \times 10^{-4}$ (linear decay to $1.0 \times 10^{-5}$) | Proven standard in discrete MARL (Yu et al., 2022) |
| **Critic Learning Rate** | $1.0 \times 10^{-3}$ (linear decay to $1.0 \times 10^{-5}$) | Faster value convergence prevents policy drift |
| **PPO Clip Parameter ($\epsilon_{\text{clip}}$)** | $0.20$ | Standard stability bound (Schulman et al., 2017) |
| **Value Loss Clip ($\epsilon_{\text{val}}$)** | $0.20$ | Prevents large value update shocks |
| **Discount Factor ($\gamma$)** | $0.995$ | Long horizon required (games average 200–500 steps) |
| **GAE Parameter ($\lambda$)** | $0.95$ | Reduces variance while bounding bias (Schulman et al., 2015) |
| **Entropy Coefficient ($c_{\text{ent}}$)** | $0.01$ (annealed to $0.001$ at 80% training) | Preserves exploratory branching early; sharpens late play |
| **Value Loss Coefficient ($c_{\text{val}}$)** | $0.50$ | Balanced gradient contribution |
| **Max Gradient Norm** | $0.5$ | Gradient clipping prevents exploding updates |
| **Rollout Buffer Horizon ($T$)** | $256$ environment steps per worker | Captures multi-turn interaction cycles |
| **Parallel Environments** | $32$ vectorized environments | Throughput optimization and batch decorrelation |
| **Total Batch Size per Update** | $32 \times 256 = 8{,}192$ transitions | Standard sample size for stable policy step |
| **PPO Mini-Batch Size** | $512$ | 16 mini-batches per epoch |
| **Optimization Epochs ($K_{\text{epoch}}$)** | $4$ | Prevents policy divergence on off-policy surrogate |
| **Action Masking Method** | Large Negative Logit Masking ($-10^8$) | Standard in discrete masked RL (Huang et al., 2022) |

#### Network Architectures:
1. **Feedforward Actor-Critic Backbone:**
   - **Observation Dimension:** $D_{\text{FF}} = 278$ (defined in Section B).
   - **Trunk Structure:** Two dense layers of $256$ units each with Layer Normalization and ELU activation.
   - **Actor Head:** Dense layer $256 \rightarrow 76$ logits.
   - **Critic Head:** Dense layer $256 \rightarrow 1$ scalar value $V(s)$.
2. **Recurrent (GRU) Actor-Critic Backbone:**
   - **Input:** Current state vector ($D_{\text{state}} = 138$) concatenated with projected history token embedding ($128$).
   - **Spatial Projection:** Dense layer $138 \rightarrow 128$ + LayerNorm + ELU.
   - **Recurrent Core:** 1-layer GRU with hidden dimension $H = 256$.
   - **Actor Head:** Dense layer $256 \rightarrow 76$ logits.
   - **Critic Head:** Dense layer $256 \rightarrow 1$ scalar value $V(s)$.

### Secondary Algorithm (Ablation): Action-Masked Deep Q-Network (DQN)
- **Replay Buffer Size:** $500{,}000$ transitions.
- **Target Network Update Frequency:** Every $2{,}000$ environment steps (hard update) or Polyak $\tau = 0.005$.
- **Exploration Schedule:** Epsilon-greedy over masked legal actions, decaying from $\epsilon = 1.0 \rightarrow 0.05$ over $1\text{M}$ steps.
- **Discount Factor:** $\gamma = 0.995$.
- **Double DQN (DDQN):** Enabled to curb overestimation bias (van Hasselt et al., 2016).
- **Dueling Architecture:** Separate value stream $V(s)$ and advantage stream $A(s, a)$ (Wang et al., 2016).

---

## B. Observation Encoding Specification

To ensure rigorous reproducibility and eliminate information leakage, the observation tensor must be constructed strictly from `PlayerObservation` without access to underlying simulator state $S_t$.

### 1. Feedforward Encoding ($\mathbf{x}_{\text{FF}} \in \mathbb{R}^{278}$)
The feedforward encoder flattens the immediate observation and a sliding history window into a fixed-length numerical vector:

| Feature Segment | Dimension | Data Representation & Normalization |
| :--- | :---: | :--- |
| **Own Hand Composition** | $54$ | Multi-hot binary vector over canonical deck ($1$ if card present in hand, $0$ otherwise). |
| **Top Discard Card** | $54$ | One-hot binary vector over canonical deck indicating $top(Q_t)$. |
| **Current Call Shape** | $6$ | One-hot vector over shapes (`CIRCLE`, `TRIANGLE`, `CROSS`, `SQUARE`, `STAR`, `WHOT`). |
| **Active Penalty Type** | $6$ | One-hot vector (`NONE`, `HOLD_ON`, `PICK_TWO`, `PICK_THREE`, `SUSPENSION`, `GENERAL_MARKET`). |
| **Active Penalty Count** | $1$ | Normalized scalar: $\min(\text{penalty\_count}, 10) / 10.0 \in [0, 1]$. |
| **Player Hand Sizes** | $4$ | Normalized integer cards held per player: $|H_j| / 54.0 \in [0, 1]$ (relative to self: self, next, across, previous). |
| **Last Card Declarations** | $4$ | Binary indicators ($1$ if player $j$ has active declaration, $0$ otherwise; ordered relative to self). |
| **Market Deck Size** | $1$ | Normalized scalar: $|M_t| / 54.0 \in [0, 1]$. |
| **Turn Context** | $4$ | Normalized step count $\min(t, 1000) / 1000.0$, relative acting seat (one-hot of self $p \in \{0..3\}$). |
| **Public Discard Card History (Window $K=5$)** | $5 \times 14 = 70$ | Last 5 played cards. Each slot: One-hot shape ($6$) + Normalized value ($1$) + Acting relative player ($4$) + Declared ($1$) + Action type ($2$). |
| **Legal Action Mask** | $74$ | Binary indicator ($1$ if action legal, $0$ otherwise; provided for critic/attention). |
| **Total Dimension ($D_{\text{FF}}$)** | **278** | Fixed-length dense vector. |

### 2. Recurrent Encoding ($\mathbf{x}_{\text{RNN}} \in \mathbb{R}^{138}$ + Sequential Event Stream)
The recurrent architecture splits the observation into a **Current State Vector** and an **Event History Sequence**:

1. **Current State Vector ($\mathbf{v}_t \in \mathbb{R}^{138}$):**
   - Own Hand ($54$)
   - Top Discard ($54$)
   - Current Call Shape ($6$)
   - Active Penalty Status ($7$: 6 one-hot type + 1 normalized count)
   - Relative Opponent Hand Sizes & Declarations ($8$: 4 hand sizes + 4 declarations)
   - Market Size ($1$)
   - Normalized Step & Relative Seat ($8$)
2. **Public Event History Stream ($e_1, e_2, \dots, e_L$):**
   - Each event serialized as a 24-dimensional token:
     - Event Type one-hot ($12$)
     - Relative Player ID one-hot ($4$)
     - Played Card Identity ($6$ shape one-hot + $1$ normalized value, or zeros if hidden draw)
     - Associated Penalty scalar ($1$)
   - Sequence length: dynamic or padded to $L = 64$ most recent public events.
3. **Recurrent Fusion:**
   - Token stream processed by GRU core ($H = 256$); final hidden state $h_t$ is fused with projected state vector $\mathbf{v}_t$ to produce policy representation $z_t \in \mathbb{R}^{256}$.

---

## C. Action Encoding and Masking

The action space is `Discrete(76)` as frozen in `whot_ml/action.py`:
- `0–48`: Ordinary card play (49 cards).
- `49–73`: WHOT wild play specifying called shape ($5 \text{ cards} \times 5 \text{ shapes} = 25$ combinations).
- `74`: `DRAW`.
- `75`: `DECLARE_LAST`.

### Strict Masking Implementation:
1. At decision step $t$, query `mask = env.action_mask(player_id)` ($\text{len}=76, \text{values} \in \{0, 1\}$).
2. Compute raw logits $\mathbf{z} \in \mathbb{R}^{76}$ from policy network.
3. Apply additive penalty mask:
   $$z^{\text{masked}}_a = \begin{cases} z_a & \text{if } \text{mask}[a] = 1 \\ -10^{8} & \text{if } \text{mask}[a] = 0 \end{cases}$$
4. Compute policy probabilities via softmax:
   $$\pi(a \mid o) = \frac{\exp(z^{\text{masked}}_a)}{\sum_{a^\prime} \exp(z^{\text{masked}}_{a^\prime})}$$
5. **Loss Computation Invariants:**
   - In PPO surrogate loss, masked logits guarantee $\pi_\theta(a_{\text{illegal}}) = 0$.
   - The policy entropy bonus $H(\pi_\theta)$ is computed **strictly over the support of legal actions**:
     $$H(\pi) = -\sum_{a \in \mathcal{A}_{\text{legal}}} \pi(a) \log \pi(a)$$
   - Renormalizing entropy over legal actions prevents artificial inflation of entropy by illegal logits.

---

## D. Self-Play Protocol

Self-play dynamics in multi-agent games can suffer from non-transitive cycling (rock-paper-scissors dynamics) or mutual policy degradation. Paper 2 specifies two distinct training protocols:

### Protocol 1: Pure Symmetric Self-Play (Primary Baseline)
- All 4 seats in the environment share parameters $\theta_t$.
- Trajectories from all 4 players are added to the centralized rollout buffer.
- Evaluates whether homogeneous self-play converges to high-level play or falls victim to the heuristic stall.

### Protocol 2: Fictitious Self-Play / Population League (PBT Extension)
To evaluate and prevent strategy cycling, an agent pool $\mathcal{P}$ is maintained:
1. **League Pool:** Initialized with `RandomLegalAgent`, `RuleBasedAgent`, and checkpoint $\theta_0$.
2. **Snapshot Cadence:** Every $500{,}000$ training steps, the active policy $\theta_t$ is snapshotted into $\mathcal{P}$.
3. **Opponent Sampling Distribution:**
   - $70\%$ probability: Current policy $\theta_t$ (self-play).
   - $20\%$ probability: Historical snapshots $\theta_{k} \sim \mathcal{P}$ (past self).
   - $10\%$ probability: Anchored heuristic (`RuleBasedAgent`).
4. **Seating Randomization:** Active training agent is assigned randomly to Seat $p \in \{0, 1, 2, 3\}$ at each episode reset.

---

## E. Training Protocol

| Parameter | Specification |
| :--- | :--- |
| **Total Frames** | $10{,}000{,}000$ environment steps per run |
| **Independent Seeds** | 5 independent training runs (Seeds: `101, 202, 303, 404, 505`) |
| **Evaluation Cadence** | Every $200{,}000$ environment steps |
| **Evaluation Episodes** | $200$ evaluation games per checkpoint against anchor baselines |
| **Checkpoint Storage** | Saved every $500{,}000$ steps (20 checkpoints per seed $\times$ 5 seeds = 100 models) |
| **Best Model Selection** | Selected based on highest win rate in asymmetric evaluation against `RuleBasedAgent` on validation seeds |
| **Hardware Target** | Containerized GPU runner (NVIDIA T4 / P100, PyTorch 2.x) |

---

## F. Evaluation Protocol

To ensure unimpeachable scientific validity:
1. **Disjoint Seed Partitions:**
   - Training Seeds: `101, 202, 303, 404, 505`.
   - Validation Tuning Seeds: `10000–10499` (500 seeds).
   - Final Held-Out Benchmark Seeds: `20000–20999` (1,000 seeds).
2. **Evaluation Tournament Matchups ($N = 1{,}000$ games per configuration):**
   - **Configuration E1 (Symmetric Self-Play):** $4 \times \text{RL}_{\text{final}}$
   - **Configuration E2 (Asymmetric Dominance):** $1 \times \text{RL}_{\text{final}}$ vs. $3 \times \text{RandomLegal}$ (`RLL-R-R-R`)
   - **Configuration E3 (Heuristic Challenge):** $1 \times \text{RL}_{\text{final}}$ vs. $3 \times \text{RuleBased}$ (`RLL-B-B-B`)
   - **Configuration E4 (Mixed Population):** $1 \times \text{RL}_{\text{final}}$ + $1 \times \text{RuleBased}$ + $2 \times \text{RandomLegal}$
   - **Configuration E5 (2-Player Heads-Up):** $1 \times \text{RL}_{\text{final}}$ vs. $1 \times \text{RuleBased}$
   - **Configuration E6 (2-Player Heads-Up):** $1 \times \text{RL}_{\text{final}}$ vs. $1 \times \text{RandomLegal}$
3. **Mandatory Seating Equity Protocol:**
   - In all asymmetric 4-player tournaments, target agent seats rotate cyclically ($0 \rightarrow 1 \rightarrow 2 \rightarrow 3$) across equal multiples of 250 games.
   - In 2-player matchups, starting player alternates strictly every game.

---

## G. Stall Diagnostic & Emergence Metrics

The central phenomenon discovered in Paper 1 was that `RuleBasedAgent` self-play induces a **$43.6\%$ truncation rate** due to retaliatory penalty loops. Paper 2 operationalizes the "escape from the stall" via the following diagnostic framework:

### 1. Primary Metric: Truncation Rate Differential ($\Delta \tau_{\text{trunc}}$)
$$\Delta \tau_{\text{trunc}} = \tau_{\text{trunc}}(\text{RL}_{\text{self-play}}) - 43.6\%$$
- **Stall Escaped:** $\tau_{\text{trunc}}(\text{RL}_{\text{self-play}}) \le 10.0\%$ ($p < 10^{-15}$, Fisher's exact test).
- **Stall Persists:** $\tau_{\text{trunc}}(\text{RL}_{\text{self-play}}) \ge 35.0\%$.

### 2. Secondary Diagnostic: Retaliatory Chain Length
- Measure average length of consecutive penalty cards played ($2, 5, 14$) without an intervening ordinary card or pass.
- In RuleBased self-play, chain length averages $>3.8$.
- Does RL learn to withhold penalty cards until an opponent declares "Last Card"?

### 3. Card-Dumping Index (CDI)
$$\text{CDI} = \frac{\sum_{t} \mathbb{I}(\text{action}_t \text{ matches shape or number without penalty})}{\sum_{t} \mathbb{I}(\text{action}_t \text{ deploys penalty card})}$$
- Tracks whether policy prioritizes reducing hand size over attacking opponents.

---

## H. Probe Analyses (for RQ3: Hidden-Hand Belief Estimation)

To understand whether RL policies internally construct latent belief states about unobserved variables, we design a supervised linear probing protocol following Alain & Bengio (2018).

### 1. Probe Objective
Predict the binary presence of each of the 54 canonical cards in opponent $j$'s hand ($y_{c, j} \in \{0, 1\}$) from frozen agent representations $z_t \in \mathbb{R}^{256}$ at decision timestep $t$.

### 2. Probe Architecture
- **Linear Probe:** Single linear transformation $W \in \mathbb{R}^{256 \times 54} + b \in \mathbb{R}^{54}$ followed by sigmoid activation $\sigma(\cdot)$.
- **Non-Linear Probe (Control):** 2-layer MLP ($256 \rightarrow 128 \rightarrow 54$) with ReLU.

### 3. Target Label Construction
- Ground truth vector $\mathbf{y}_j(t) \in \{0, 1\}^{54}$ where $y_{c, j} = 1 \iff c \in H_j(t)$.
- Crucial invariant: Probes are trained strictly offline on frozen activations; gradients are never backpropagated into the RL policy network.

### 4. Baseline Reference Probes:
1. **Marginal Frequency Baseline:** Predicts card presence purely based on empirical card frequency in the deck.
2. **Public Counting Baseline (Heuristic Tracker):** Computes explicit known card exclusions ($C_{\text{known}} = H_{\text{self}} \cup Q_t$) and predicts uniform probability over all unseen cards:
   $$P(c \in H_j) = \frac{|H_j|}{|C_{\text{unseen}}|}$$
3. **Feedforward Probe:** Probe trained on the feedforward RL network representation.

### 5. Evaluation Metrics:
- **Macro AUROC:** Area under the ROC curve averaged across all cards.
- **Precision@K:** Precision of top-$K$ most probable cards predicted for an opponent hand of size $K = |H_j|$.

---

## I. Statistical Analysis & Significance Thresholds

1. **Win Rate Confidence Intervals:** Wilson score 95% confidence intervals reported for all proportions.
2. **Paired Seed Comparisons:** Wilcoxon signed-rank tests across the 5 independent random training seeds for all continuous performance metrics.
3. **Hypothesis Testing:**
   - Win rate dominance: One-tailed binomial test against fair-share $25.0\%$ (or $50.0\%$ in 2P).
   - Truncation reduction: $2 \times 2$ Fisher's exact test comparing truncation counts against Paper 1 baseline ($436 / 1000$).
4. **Minimum Detectable Effect Size (MDE):**
   - At $N = 1{,}000$ evaluation games and $\alpha = 0.05, \text{Power} = 0.95$, the apparatus is powered to detect a minimum win rate difference of $\pm 3.1\%$ and a truncation shift of $\pm 3.5\%$.

---

## J. Reproducibility & Open Science Protocol

1. **Simulator Freeze:** Simulator code pinned strictly to commit `7c1a2dc`.
2. **Environment Determinism:** 100% bitwise reproducibility verified via random seed logging.
3. **Artifact Repository Structure for Paper 2:**
   ```text
   experiments/paper2/
   ├── configs/             # PPO and DQN hyperparameter YAML manifests
   ├── src/                 # Observation encoders, policy nets, probe definitions
   ├── runners/             # Training and evaluation orchestration scripts
   ├── checkpoints/         # Saved PyTorch model weights (.pt)
   ├── raw/                 # Evaluation tournament JSONL logs
   ├── processed/           # Aggregated statistics and probe accuracy CSVs
   ├── figures/             # Vector publication figures (PDF / PNG)
   └── tables/              # LaTeX tables and markdown summaries
   ```
4. **Random Seed Registry:**
   - Training Seeds: `101, 202, 303, 404, 505`.
   - Tournament Seeds: `20000–20999`.

---

## K. Compute Budget & Platform Execution Plan

| Stage | Hardware Target | Runs / Epochs | Estimated Wall Time | GPU Hours |
| :--- | :--- | :--- | :--- | :--- |
| **PPO Seed 1–5 (10M steps)** | Kaggle GPU (T4 / P100) | 5 seeds $\times$ 10M frames | $\approx 3.0$ hrs / seed | 15.0 hrs |
| **Ablation: Feedforward vs GRU** | Kaggle GPU (T4 / P100) | 3 seeds $\times$ 5M frames | $\approx 1.5$ hrs / seed | 4.5 hrs |
| **Ablation: PPO vs DQN** | Kaggle GPU (T4 / P100) | 3 seeds $\times$ 5M frames | $\approx 2.0$ hrs / seed | 6.0 hrs |
| **Evaluation Tournaments** | CPU (Multi-core) | $25{,}000$ games total | $\approx 6.0$ hrs | 0.0 hrs |
| **Probe Training & Eval** | Kaggle GPU | 50K transitions | $\approx 1.5$ hrs | 1.5 hrs |
| **Total Compute Budget** | | | | **27.0 GPU hrs** |

*Platform Note:* Within standard Kaggle weekly GPU quota (30 hours/week) or runnable in two staged dispatches.

---

## L. Failure Modes & Scientific Value Matrix

| Failure Mode | Empirical Manifestation | Scientific Value & Framing | Publishable? |
| :--- | :--- | :--- | :--- |
| **1. Policy Stalls Completely** | Truncation remains $\approx 43\%$ or increases to $>50\%$. Self-play policies mirror heuristic retaliatory loops. | Demonstrates that the defensive stall is an intrinsic game-theoretic trap of WHOT rather than a heuristic bug. Establishes WHOT as a formidable benchmark requiring non-myopic planning (MCTS/CFR). | **YES** |
| **2. Trivial Policy Collapse** | Agent hoards penalty cards or learns degenerate pass/draw loops to avoid penalties. | Exposes multi-agent pathology; provides baseline for why standard model-free RL fails in card games with penalty loops without belief modeling. | **YES** |
| **3. Lack of Latent Representation** | Probes fail to predict opponent hands (AUROC $\approx 0.50$). | Confirms that standard model-free RL policies in POMDPs rely on surface heuristics rather than true belief state reconstruction. Directly motivates Paper 3 (explicit auxiliary belief training). | **YES** |
| **4. Substandard Win Rates vs. Heuristic** | Self-play RL loses to `RuleBasedAgent` ($<25\%$ win rate). | Identifies out-of-distribution vulnerability and strategic specialization in self-play. Provides quantitative benchmark floor. | **YES** |

*Scientific Takeaway:* In all possible outcomes, a rigorous negative result is equally as scientifically valuable as a positive result.

---

# 4. Definition of a Successful Paper 2

A successful Paper 2 requires:
1. **Definitive Answer to All Four RQs:** Rigorous empirical proof supporting or refuting each hypothesis with exact confidence intervals.
2. **Unbroken Simulator Freeze:** 100% adherence to frozen commit `7c1a2dc`.
3. **Exposing RL Behavior in Imperfect Information:** Clear characterization of how policy entropy, game duration, and special action distributions evolve under self-play.
4. **Quantified Belief Probing:** Concrete measurement of whether recurrent models learn implicit card counting without auxiliary supervision.
5. **Direct Scientific Bridge to Paper 3:** Providing the benchmark baseline that justifies Paper 3's auxiliary belief-learning architectures.

---

# 5. Review & Approval Protocol

- Document must be formally reviewed and approved before any Python training script or network model is implemented in `experiments/paper2/`.
- No modifications may be committed to `whot_ml/`.
