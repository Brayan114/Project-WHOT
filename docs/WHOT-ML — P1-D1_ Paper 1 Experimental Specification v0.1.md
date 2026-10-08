# WHOT-ML — P1-D1: Paper 1 Experimental Specification v0.1

## Status

- **Phase:** Phase 1 — Paper 1 Empirical Foundation
- **Document:** P1-D1 — Paper 1 Experimental Specification
- **Version:** 0.1
- **Baseline Simulator:** WHOT-NG-v1.0 (Commit `7c1a2dc`, frozen)
- **Baseline Environment:** `WHOT-NG-v1`
- **Validation Status:** 96 baseline tests passing (100% pass rate)
- **Document Status:** PLANNED EXPERIMENTAL PROTOCOLS (Distinguished strictly from observed results)

---

# 1. Executive Summary & Core Principles

This specification formalizes the empirical methodology and experimental apparatus for:

> **“WHOT-ML: A Configurable Partially Observable Multi-Agent Environment for Machine Learning Research.”**

### 1.1 Non-Negotiable Simulator Freeze Invariant
The simulator `WHOT-NG-v1.0` is an immutable experimental instrument:
1. Files under `whot_ml/` MUST NOT be modified, patched, refactored, or tuned.
2. The baseline ruleset (`WHOTConfig` default), card ontology (54 cards), 76-slot action mask, observation isolation model (`ObservationGenerator`), effect resolver, and event emission pipeline are strictly frozen.
3. All telemetry collection, trajectory recording, equivalence generators, seat rotators, paired statistical evaluators, plotters, and table formatters must live outside `whot_ml/` under `experiments/paper1/` and `tests/`.
4. If an experiment encounters unexpected behavior, it must be documented as an empirical finding or verified against the Phase 0 specification; the simulator must never be altered to make an experiment simpler or distributions more aesthetically pleasing.

### 1.2 Separation of Planned Protocols vs. Observed Results
This document defines **planned protocols only**. It does not contain fabricated or anticipated numerical outcomes. All empirical numbers reported during apparatus validation are strictly designated as **PILOT** data and must not be cited as definitive paper conclusions.

---

# 2. Formal Information Metrics & Ontology

To prevent ambiguity, all informational and state metrics are mathematically grounded in the formal state definition $S_t = (H_t, M_t, Q_t, C_t, K_t, E_t, L_t, \tau_t, R)$ and observation definition $\Omega_p(S_t)$:

### 2.1 Card Partitions
The canonical deck contains $C_{total} = 54$ physical cards. At any timestep $t$:
1. **Publicly Visible Cards ($C_{pub}(t)$):** Cards visible on the discard play pile $Q_t$. The top card $top(Q_t)$ governs legal plays; the remaining cards in $Q_t$ are publicly observable in the event history.
2. **Privately Known Cards for Player $p$ ($C_{priv, p}(t)$):** Cards currently held in player $p$'s private hand $H_p(t)$.
3. **Opponent-Hidden Cards for Player $p$ ($C_{opp, p}(t)$):** Cards held by all opponents:
   $$C_{opp, p}(t) = \bigcup_{j \neq p} H_j(t)$$
4. **Market-Hidden Cards ($C_{mkt}(t)$):** Cards residing in the unexhausted draw market $M_t$.
5. **Known Card Identities to Player $p$ ($C_{known, p}(t)$):**
   $$C_{known, p}(t) = C_{priv, p}(t) \cup Q_t$$
6. **Unseen Card Identities to Player $p$ ($C_{unseen, p}(t)$):**
   $$C_{unseen, p}(t) = C_{total} \setminus C_{known, p}(t) = C_{opp, p}(t) \cup M_t$$

### 2.2 Information vs. Count Uncertainty
- **Card Count Knowledge:** In $\Omega_p(S_t)$, the exact integer counts $|H_j(t)|$ for all players $j$ and the market size $|M_t|$ are publicly observable.
- **Card Identity Uncertainty:** Player $p$ knows that the set $C_{unseen, p}(t)$ of size $54 - |H_p(t)| - |Q_t|$ is partitioned into $|H_j(t)|$ cards for each opponent $j$ and $|M_t|$ cards in the draw pile, but has zero direct visibility into which card belongs to which partition.
- **Card Sequence / Ordering Uncertainty:** The exact permutation of the $|M_t|$ cards in $M_t$ is hidden from all players.
- **Opponent-to-Market Ratio ($\rho_{opp/mkt}(t)$):**
  $$\rho_{opp/mkt}(t) = \frac{\sum_{j \neq p} |H_j(t)|}{|M_t|}$$
  At initial deal ($t=0$, each player has 6 cards, 1 card on play pile):
  - For $N=2$: $|C_{opp}| = 6$, $|M| = 41 \implies \rho = 6/41 \approx 0.146$
  - For $N=3$: $|C_{opp}| = 12$, $|M| = 35 \implies \rho = 12/35 \approx 0.343$
  - For $N=4$: $|C_{opp}| = 18$, $|M| = 29 \implies \rho = 18/29 \approx 0.621$
  - For $N=5$: $|C_{opp}| = 24$, $|M| = 23 \implies \rho = 24/23 \approx 1.043$
  - For $N=6$: $|C_{opp}| = 30$, $|M| = 17 \implies \rho = 30/17 \approx 1.765$

---

# 3. Experimental Data Lifecycle & Manifest Architecture

Every experiment follows a four-stage pipeline:
```text
Frozen Simulator (whot_ml)
          │
          ▼
Raw Telemetry (experiments/paper1/raw/*.jsonl)
          │
          ▼
Derived Metrics (experiments/paper1/processed/*.json, *.csv)
          │
          ▼
Presentation Data (experiments/paper1/figures/*.png, tables/*.md, *.tex)
```

### 3.1 Mandatory Execution Manifest
Every run (pilot and full) must write an immutable machine-readable manifest:
```json
{
  "manifest_version": "1.0",
  "experiment_id": "EXP-01-CHAR-001",
  "is_pilot": true,
  "timestamp_utc": "2026-10-04T20:25:00Z",
  "simulator_version": "1.0.0",
  "simulator_commit": "7c1a2dc",
  "baseline_environment": "WHOT-NG-v1.0",
  "variant_id": "BASE",
  "variant_parent": "WHOT-NG-v1",
  "ruleset_hash": "sha256:...",
  "config_hash": "sha256:...",
  "agent_population": ["RuleBasedAgent", "RandomLegalAgent"],
  "player_count": 4,
  "seed_range": [10000, 10049],
  "seat_protocol": "CYCLIC_ROTATION",
  "starter_policy": "RANDOM",
  "num_runs": 50,
  "platform_info": {
    "os": "Windows",
    "python_version": "3.9.13",
    "pytest_version": "8.4.2"
  }
}
```

---

# 4. Detailed Experiment Specifications

---

## 4.1 EXP-01 — Environment Characterization

### 1. Research Question
**RQ1:** What are the fundamental structural and behavioral distributions of WHOT-NG-v1 across decision states, turn durations, card draws, and special-card activations under baseline play?

### 2. Hypothesis
Decision branching $|A(s_t)|$ is tightly constrained ($|A(s_t)| \ll 76$), while game length exhibits a right-skewed distribution governed by special-card interventions (Hold On, Penalties, Suspensions, and Market Reshuffles).

### 3. Purpose
Establish the fundamental empirical baseline of the environment for theoretical reference, game-tree complexity analysis, and reinforcement learning state-action sizing.

### 4. Independent Variables
None. The environment is fixed to baseline WHOT-NG-v1.

### 5. Dependent Variables
- **Per-Step Metrics:**
  - Legal action count $|A(s_t)|$ per active decision
  - Action type selected per step ($\text{PLAY}, \text{PLAY\_WHOT}, \text{DRAW}, \text{DECLARE\_LAST}$)
  - Hand size of acting player $|H_i(t)|$
  - Active penalty stack size at step $t$
- **Per-Game Metrics:**
  - Total turn count $T$ to termination
  - Total discrete timesteps $\tau$
  - Draw count per game $D_{total}$
  - Special card activations: WHOT ($N_{20}$), Pick Two ($N_2$), Pick Three ($N_5$), Hold On ($N_1$), Suspension ($N_8$), General Market ($N_{14}$)
  - Market reshuffle count $R_{mkt}$
  - Declaration violations $V_{decl}$
  - Termination status (clean terminal vs truncated at 1,000 turns)
- **Per-Player Metrics:**
  - Final hand size $|H_i(T)|$
  - Victory outcome ($\mathbb{I}[\text{winner} == i]$)
  - Cards drawn per player $D_i$
  - Special cards played per player

### 6. Controlled Variables
- Ruleset: Baseline `WHOTConfig(ruleset_name="WHOT-NG-v1", player_count=4)`
- Starting hand size: 6 cards
- Starter policy: `StarterPolicy.RANDOM`
- Max turns limit: 1,000

### 7. Exact Environment Configuration
```python
WHOTConfig(
    ruleset_name="WHOT-NG-v1",
    player_count=4,
    starting_hand_size=6,
    turn_direction=TurnDirection.CLOCKWISE,
    starter_policy=StarterPolicy.RANDOM,
    pick_two_enabled=True,
    pick_two_stacking=StackingMode.SAME_EFFECT,
    pick_three_enabled=True,
    pick_three_stacking=StackingMode.SAME_EFFECT,
    hold_on_enabled=True,
    suspension_enabled=True,
    general_market_enabled=True,
    last_card_declaration_enabled=True,
    last_card_violation_penalty=LastCardViolationPenalty.DRAW_1,
    final_card_one_policy=FinalCardOnePolicy.REJECT_LEGALITY,
    maximum_turns=1000
)
```

### 8. Agent Configurations
Evaluated across two reference cohorts:
- **Cohort 1 (Stochastic Reference):** 4 $\times$ `RandomLegalAgent(seed=seed+p)`
- **Cohort 2 (Heuristic Reference):** 4 $\times$ `RuleBasedAgent(seed=seed+p)`

### 9. Number of Games / Runs
- **Pilot Configuration:** 50 games per cohort ($2 \times 50 = 100$ total games).
- **Full-Experiment Configuration:** 1,000 games per cohort ($2 \times 1,000 = 2,000$ total games).

### 10. Seed Protocol
Deterministic linear sequence:
- Cohort 1 Seeds: `10000` to `10000 + N_games - 1`
- Cohort 2 Seeds: `11000` to `11000 + N_games - 1`

### 11. Seat / Start-Player Protocol
Starter assigned randomly via simulator RNG per seed (`StarterPolicy.RANDOM`). Agents occupy seats 0 to 3 uniformly.

### 12. Data Collected
- Complete event stream per game (JSONL)
- Step telemetry: $(t, p, |A(s_t)|, a_t, |H_p(t)|, |M_t|)$
- Episode summary metrics record (JSON)

### 13. Metric Definitions & Mathematical Formulas
- **Mean Legal Actions:** $\mu_{|A|} = \frac{1}{\sum T_g} \sum_{g} \sum_{t} |A(s_{g,t})|$
- **Draw Rate:** $r_{draw} = \frac{\sum D_g}{\sum T_g}$
- **Truncation Rate:** $\hat{p}_{trunc} = \frac{1}{G} \sum_{g=1}^G \mathbb{I}[\text{truncated}_g]$ with 95% Wilson score interval:
  $$CI_{95\%} = \frac{\hat{p} + \frac{z^2}{2G} \pm z\sqrt{\frac{\hat{p}(1-\hat{p})}{G} + \frac{z^2}{4G^2}}}{1 + \frac{z^2}{G}} \quad (z = 1.96)$$

### 14. Statistical Summaries
Sample size $n$, Mean, Standard Deviation, Median, IQR, Minimum, Maximum, Skewness, ECDF for legal actions and game length.

### 15. Required Figures
- **Figure 1A:** Empirical probability mass of legal actions $|A(s_t)|$ comparing Random vs RuleBased.
- **Figure 1B:** Game length distribution (turns) with overlaid median and IQR markers.
- **Figure 1C:** Average hand size trajectory $\bar{|H(t)|}$ normalized by episode completion percentage.

### 16. Required Tables
- **Table 1:** Comprehensive baseline environment characterization table (Action space size, mean legal actions, mean turns, draw rate, special card frequencies, truncation rate).

### 17. Expected Interpretation
Establishes that WHOT has high dynamic action variance and that heuristic play shortens episode length and reduces draw rates relative to uniform random play.

### 18. Failure Conditions
- Any illegal action executed.
- Card conservation invariant violated: $|M_t| + |Q_t| + \sum |H_i(t)| \neq 54$.
- Truncation rate $> 5\%$ under baseline play.

### 19. Reproducibility Requirements
Identical trajectories reproduced bit-for-bit from manifest seed list.

---

## 4.2 EXP-02 — Partial Observability Demonstration

### 1. Research Question
**RQ2:** Can we rigorously prove and empirically demonstrate that distinct complete world states $S_a \neq S_b$ map to identical player observations $\Omega_p(S_a) = \Omega_p(S_b)$, and that these observationally indistinguishable states produce diverging future trajectories?

### 2. Hypothesis
Because opponent hands and draw-market ordering reside behind the observation boundary, there exists a large set of observationally equivalent complete states that cannot be distinguished by player $p$ but yield distinct future outcomes.

### 3. Purpose
Provide formal, empirical, and leak-free proof of partial observability in WHOT-NG-v1, demonstrating that the environment provides genuine hidden information rather than merely an incomplete API.

### 4. Independent Variables
Constructed hidden-state variations:
- Mode A: Swapping unobserved cards between opponent hands $H_j$ and $H_k$ ($j, k \neq p$) while preserving hand sizes.
- Mode B: Permuting the internal sequence of cards in the unobserved market $M$.
- Mode C: Swapping an unobserved card between an opponent hand $H_j$ and the market $M$.

### 5. Dependent Variables
- Observation equivalence check: $\Omega_p(S_a) == \Omega_p(S_b)$ (Bitwise / key-value dictionary equality).
- Hidden state difference: $S_a \neq S_b$ (Explicit diff identification: which card moved where).
- Information leakage check: Confirmation that no opponent card IDs appear in $\Omega_p$.
- Controlled combinatorial estimation of compatible hidden configurations $|\hat{\mathcal{S}}(\Omega)|$.
- Future trajectory divergence step $k_{div}$: First step where public events or observations diverge under fixed policy execution.

### 6. Controlled Variables
- Player index $p = 0$ as the observing agent.
- Visible state components identical in $S_a$ and $S_b$: $H_p$, top card $top(Q)$, current call $C_t$, penalty state $E_t$, public history.

### 7. Exact Environment Configuration
Baseline `WHOTConfig(ruleset_name="WHOT-NG-v1", player_count=4)`.

### 8. Agent Configurations
Trajectories rolled out from $S_a$ and $S_b$ using deterministic `RandomLegalAgent(seed=42)` and `RuleBasedAgent(seed=42)`.

### 9. Number of Games / Runs
- **Pilot Configuration:** 10 genuine game trajectories sampled at timesteps $t \in \{5, 10, 15\}$, generating 30 controlled state pairs $(S_a, S_b)$.
- **Full-Experiment Configuration:** 50 game trajectories sampled across early ($t=5$), middle ($t=15$), and late ($t=25$) stages, generating 150 controlled pairs.

### 10. Seed Protocol
Seeds `20000` to `20049` for generating source game trajectories; fixed rollout seed `42` for divergence verification.

### 11. Seat / Start-Player Protocol
Target player $p=0$; starter assigned by baseline rules.

### 12. Data Collected
- Full serialized state dictionaries for $S_a$ and $S_b$.
- Serialized observation dictionary $\Omega_p$.
- Explicit diff report: `diff(S_a, S_b)`.
- Divergence trace: $(k_{div}, \text{event}_a(k_{div}), \text{event}_b(k_{div}))$.

### 13. Metric Definitions & Mathematical Formulas
- **Observational Equivalence Invariant:**
  $$\Omega_p(S_a) = \Omega_p(S_b) \iff \text{to\_dict}(\Omega_p(S_a)) \equiv \text{to\_dict}(\Omega_p(S_b))$$
- **Combinatorial Compatibility Estimate:**
  Given $U = |C_{unseen, p}(t)|$ unobserved cards partitioned into opponent hands of sizes $h_1, h_2, \dots, h_{N-1}$ and market size $m$:
  $$|\hat{\mathcal{S}}(\Omega)| = \frac{U!}{h_1! h_2! \dots h_{N-1}! m!} \times m! = \frac{U!}{\prod_{j \neq p} h_j!}$$
  Log-uncertainty metric:
  $$\mathcal{U}(\Omega) = \log_{10} |\hat{\mathcal{S}}(\Omega)| = \log_{10}(U!) - \sum_{j \neq p} \log_{10}(h_j!)$$

### 14. Statistical Summaries
- Mean and median $\mathcal{U}(\Omega)$ at game phases ($t=5, 15, 25$).
- Distribution of trajectory divergence step $k_{div}$ across pairs.
- Equivalence verification rate (must be 100%).
- Information leakage rate (must be 0.0%).

### 15. Required Figures
- **Figure 2:** Visual state-observation mapping schematic: Complete states $S_a$ vs $S_b$ displaying private hands, market ordering, and the identical filtered observation $\Omega_0$.
- **Figure 3:** Histogram of steps to divergence $k_{div}$ comparing hand swaps vs market permutations.

### 16. Required Tables
- **Table 2:** Combinatorial hidden uncertainty metrics across early, mid, and late game stages (Unseen card count, log compatibility size, divergence frequency).
- **Representative Case Studies:** Full JSON records of 3 concrete pairs suitable for paper inclusion.

### 17. Expected Interpretation
Confirms that agents operating under partial observability must reason under substantial hidden-state equivalence classes.

### 18. Failure Conditions
- $\Omega_p(S_a) \neq \Omega_p(S_b)$ (construction error).
- Any opponent card ID found in $\Omega_p$.
- Claiming optimal action differences without an optimal-action oracle.

### 19. Reproducibility Requirements
Controlled pairs generated deterministically from seed and midpoint step index.

---

## 4.3 EXP-03 — Baseline Agent Characterization

### 1. Research Question
**RQ3:** What behavioral regimes, win rates, and game lengths emerge from non-learning baseline agents (`RandomLegalAgent` vs `RuleBasedAgent`) under controlled seat assignments?

### 2. Hypothesis
`RuleBasedAgent` will win significantly more games, achieve higher finishing ranks, suffer zero declaration violations, and maintain smaller average hand sizes than `RandomLegalAgent`.

### 3. Purpose
Establish the experimental behavioral floor and benchmark reference points for subsequent learning agents (reinforcement learning, self-play).

### 4. Independent Variables
Agent population matchup:
- Population 1: 4 $\times$ `RandomLegalAgent` (RRRR)
- Population 2: 4 $\times$ `RuleBasedAgent` (BBBB)
- Population 3: 1 $\times$ `RuleBasedAgent` vs 3 $\times$ `RandomLegalAgent` (BRRR, with B rotated across all 4 seats)
- Population 4 (2-Player): 1 $\times$ `RuleBasedAgent` vs 1 $\times$ `RandomLegalAgent` (BR, alternating starter)

### 5. Dependent Variables
- Win rate $\hat{w}_i$ per agent seat and per agent type
- Average finishing position (1st to 4th based on final hand size)
- Episode length in turns
- Draw frequency per game
- Special card utilization rate
- Last-card declaration violation rate
- Truncation rate

### 6. Controlled Variables
- Ruleset: Baseline `WHOTConfig(player_count=4)` (and $N=2$ for Pop 4)
- Fixed starting hand size: 6 cards

### 7. Exact Environment Configuration
Baseline `WHOTConfig` default.

### 8. Agent Configurations
- `RandomLegalAgent(name=f"Random-{p}")`
- `RuleBasedAgent(name=f"RuleBased-{p}")`

### 9. Number of Games / Runs
- **Pilot Configuration:**
  - RRRR: 20 games
  - BBBB: 20 games
  - BRRR: 40 games (10 games per seat position 0, 1, 2, 3)
  - BR (2-player): 20 games (10 games per starter)
  - Total Pilot: 100 games.
- **Full-Experiment Configuration:**
  - RRRR: 1,000 games
  - BBBB: 1,000 games
  - BRRR: 2,000 games (500 games per seat position)
  - BR (2-player): 1,000 games (500 games per starter)
  - Total Full: 5,000 games.

### 10. Seed Protocol
Contiguous deterministic seed block: `30000` to `30000 + N_games - 1`.

### 11. Seat / Start-Player Protocol
Balanced cyclic seat rotation: In game $g$, target agent occupies seat $s = g \pmod N$. Starting player selected randomly by simulator seed.

### 12. Data Collected
- Episode summary dictionary per game
- Seating map: `{seat_idx: agent_name}`
- Final hand sizes and ranks

### 13. Metric Definitions & Mathematical Formulas
- **Finishing Rank:** For player $p$, rank $R_p \in \{1, \dots, N\}$ ordered ascending by final hand size $|H_p(T)|$, with ties sharing the average rank.
- **Agent Win Rate:** $\hat{w}_A = \frac{\sum_{g} \mathbb{I}[\text{winner}_g \in \text{Seats}(A)]}{G_A}$ with 95% Wilson confidence interval.

### 14. Statistical Summaries
Mean, Std, Median, IQR of turns; Win rates with Wilson CIs; Average rank per agent type.

### 15. Required Figures
- **Figure 4:** Win rate bar plot with 95% Wilson error bars for BRRR and BR tournaments.
- **Figure 5:** Finishing position distribution (stacked bar chart: 1st, 2nd, 3rd, 4th).
- **Figure 6:** Mean hand-size progression curves over normalized turns for Random vs RuleBased.

### 16. Required Tables
- **Table 3:** Baseline tournament summary (Agent matchup, Win %, 95% CI, Avg Rank, Avg Turns, Draw Rate, Declaration Violations, Truncation %).

### 17. Expected Interpretation
Quantifies the performance gap between random play and simple tactical heuristics without claiming superhuman capability.

### 18. Failure Conditions
- `RuleBasedAgent` committing a declaration violation (violates heuristic priority 1).
- Significant seating bias in homogenous matches (tested via Chi-square goodness-of-fit).

### 19. Reproducibility Requirements
Exact match outcomes reproduced given seed and agent seat mapping.

---

## 4.4 EXP-04 — Player Count Scaling

### 1. Research Question
**RQ4:** How do game duration, card distributions, draw frequencies, and hidden information metrics scale as the number of participating players varies across $N \in \{2, 3, 4, 5, 6\}$?

### 2. Hypothesis
Increasing $N$ shifts cards from the draw market into opponent hands, increasing the opponent-to-market ratio $\rho_{opp/mkt}$, while total game duration scales non-linearly due to increased special-card interactions.

### 3. Purpose
Characterize how multi-agent population scaling alters the computational and strategic landscape of WHOT-NG-v1.

### 4. Independent Variables
Player count $N \in \{2, 3, 4, 5, 6\}$.

### 5. Dependent Variables
- Total episode duration (turns)
- Turns per player: $T_{player} = T / N$
- Cards drawn per game and per player: $D_{total}$ and $D / N$
- Initial and mean opponent-to-market ratio $\rho_{opp/mkt}$
- Market reshuffle frequency per game
- Truncation frequency

### 6. Controlled Variables
- Ruleset: WHOT-NG-v1 baseline configuration.
- Starting hand size: 6 cards per player.
- Population: Homogenous `RuleBasedAgent` population (and comparative `RandomLegalAgent` cohort).

### 7. Exact Environment Configuration
`WHOTConfig(ruleset_name="WHOT-NG-v1", player_count=N)` for $N \in \{2, 3, 4, 5, 6\}$.

### 8. Agent Configurations
Homogenous `RuleBasedAgent` population of size $N$.

### 9. Number of Games / Runs
- **Pilot Configuration:** 20 games per player count ($5 \times 20 = 100$ games).
- **Full-Experiment Configuration:** 500 games per player count ($5 \times 500 = 2,500$ games).

### 10. Seed Protocol
Identical seed offsets across player counts: seeds `40000` to `40000 + N_games - 1` reused for each $N$ to enable direct cross-scale comparisons.

### 11. Seat / Start-Player Protocol
Uniform seat assignment; random starter policy.

### 12. Data Collected
Episode metrics, initial market size, final hand sizes, total draws.

### 13. Metric Definitions & Mathematical Formulas
- **Initial Market Size:** $|M_0| = 54 - 6N - 1$
- **Initial Hidden Opponent Cards:** $|C_{opp, 0}| = 6(N-1)$
- **Initial Information Ratio:**
  $$\rho_0(N) = \frac{6(N-1)}{53 - 6N}$$
- **Normalized Turn Count:** $T_{norm} = T / N$

### 14. Statistical Summaries
Mean, Std, Median, IQR of turns and draws by $N$; OLS regression slope of $T$ vs $N$ and $T_{norm}$ vs $N$.

### 15. Required Figures
- **Figure 7:** Total game duration $T$ and per-player duration $T/N$ vs Player Count $N$ (box plots with median lines).
- **Figure 8:** Theoretical and empirical hidden card partition (Opponent hands vs Draw Market) across $N \in \{2, 3, 4, 5, 6\}$.

### 16. Required Tables
- **Table 4:** Player count scaling summary table ($N$, Initial $|M|$, Initial $|C_{opp}|$, Mean Turns, Turns/Player, Draws/Game, Reshuffles/Game, Truncation Rate).

### 17. Expected Interpretation
Demonstrates how the strategic nature of WHOT shifts from market-dominated uncertainty at $N=2$ to opponent-dominated uncertainty at $N=6$.

### 18. Failure Conditions
- Initial deal failure at $N=6$ (must verify $54 - 36 - 1 = 17 > 0$).
- Disproportionate truncation surge ($> 10\%$).

### 19. Reproducibility Requirements
All runs reproduced from seed and $N$.

---

## 4.5 EXP-05 — Controlled Rule Variants

### 1. Research Question
**RQ5:** How do isolated rule modifications (disabling penalty stacking, disabling last-card declarations, or altering violation penalties) alter game length, draw dynamics, and victory distributions relative to the frozen baseline?

### 2. Hypothesis
Disabling penalty stacking will reduce extreme draw spikes and compress game length variance; disabling last-card declaration will eliminate declaration penalties and shift victory distributions toward aggressive offensive play.

### 3. Purpose
Demonstrate the configurable nature of the WHOT-ML laboratory by measuring environmental sensitivity to individual rule switches.

### 4. Independent Variables
Derived ruleset configurations:
1. `VAR-BASE` (Baseline WHOT-NG-v1)
2. `VAR-NO-STACK-2`: `pick_two_stacking = StackingMode.NO_STACKING`
3. `VAR-NO-STACK-3`: `pick_three_stacking = StackingMode.NO_STACKING`
4. `VAR-NO-DECL`: `last_card_declaration_enabled = False`
5. `VAR-PENALTY-2`: `last_card_violation_penalty = LastCardViolationPenalty.DRAW_2`

### 5. Dependent Variables
- Game length (turns)
- Total cards drawn per game
- Maximum penalty stacked during episode: $\max_t(\text{active\_penalty\_count}_t)$
- Declaration violation count
- Truncation rate

### 6. Controlled Variables
- Player count: $N = 4$
- Agent population: 1 $\times$ `RuleBasedAgent` (Seat 0) vs 3 $\times$ `RandomLegalAgent` (Seats 1, 2, 3)
- Seed sequence: Matched identical seeds across all variants.

### 7. Exact Environment Configuration
Derived configurations inheriting from baseline with exactly one modified attribute.

### 8. Agent Configurations
1 $\times$ `RuleBasedAgent`, 3 $\times$ `RandomLegalAgent`.

### 9. Number of Games / Runs
- **Pilot Configuration:** 20 games per variant ($5 \times 20 = 100$ games).
- **Full-Experiment Configuration:** 500 games per variant ($5 \times 500 = 2,500$ games).

### 10. Seed Protocol
Strict matched-seed protocol: Seeds `50000` to `50000 + N_games - 1` applied identically across all 5 configurations to ensure valid paired statistical testing.

### 11. Seat / Start-Player Protocol
Fixed seat assignments across matched seeds to isolate rule effects from seating noise.

### 12. Data Collected
Paired episode records: `(seed, metric_base, metric_variant)`.

### 13. Metric Definitions & Mathematical Formulas
- **Paired Difference:** $\Delta X_g = X_{variant, g} - X_{base, g}$
- **Paired Wilcoxon Signed-Rank Test:** Testing null hypothesis $H_0: \text{median}(\Delta X) = 0$.
- **Effect Size (Cliff's Delta):**
  $$d = \frac{\#(\Delta X > 0) - \#(\Delta X < 0)}{G}$$

### 14. Statistical Summaries
Mean, Std, Median, IQR of metrics per variant; Paired mean difference $\bar{\Delta}$, Wilcoxon $W$ and $p$-value, Cliff's delta.

### 15. Required Figures
- **Figure 9:** Kernel Density Estimation (KDE) comparison of game length across rule variants.
- **Figure 10:** Empirical distribution of maximum penalty stacks (VAR-BASE vs VAR-NO-STACK).

### 16. Required Tables
- **Table 5:** Rule ablation comparison table (Variant ID, Rule change, Mean Turns, $\Delta$ Turns, $p$-value, Mean Draws, Max Stack, Truncation %).

### 17. Expected Interpretation
Validates that each rule switch produces statistically significant and strategically interpretable shifts in environment behavior.

### 18. Failure Conditions
- Unmatched seeds across variant comparisons.
- Accidental in-place mutation of the baseline `WHOTConfig` instance.

### 19. Reproducibility Requirements
Exact paired differences reproduced using identical matched seeds.

---

## 4.6 EXP-06 — Determinism and Reproducibility

### 1. Research Question
**RQ6:** Does WHOT-NG-v1 guarantee bitwise-exact trajectory reproducibility and event-by-event equivalence across independent replays and mid-game checkpoint restoration?

### 2. Hypothesis
WHOT-NG-v1 is strictly deterministic: identical seeds and configurations produce 100% bitwise-identical event sequences, state trajectories, and reward vectors; restoring state from mid-game checkpoints yields continuations identical to uninterrupted runs.

### 3. Purpose
Verify the mathematical rigor and software engineering reliability of the simulator as a scientific instrument.

### 4. Independent Variables
- Sub-Protocol 6A: Independent execution repeat (Run 1 vs Run 2 from same seed).
- Sub-Protocol 6B: Execution mode (Uninterrupted Run vs Mid-Game Checkpoint Restored Run).

### 5. Dependent Variables
- Event-by-event trajectory match indicator:
  $$\mathbb{I}[T_{orig} \equiv T_{replay}]$$
- Checkpoint continuation match indicator:
  $$\mathbb{I}[T_{uninterrupted}[k:] \equiv T_{restored}[k:]]$$
- Reproduction Success Rate (RSR):
  $$\text{RSR} = \frac{N_{identical}}{N_{total}} \times 100\%$$

### 6. Controlled Variables
- Ruleset: Baseline WHOT-NG-v1.
- Agent lineup: 4 $\times$ `RandomLegalAgent`.

### 7. Exact Environment Configuration
Baseline `WHOTConfig` default.

### 8. Agent Configurations
Deterministic `RandomLegalAgent` initialized with fixed per-player seeds.

### 9. Number of Games / Runs
- **Pilot Configuration:**
  - Sub-Protocol 6A (Replay): 20 games.
  - Sub-Protocol 6B (Checkpoint): 20 games (checkpointed at turn $k=10$).
  - Total Pilot: 40 tests.
- **Full-Experiment Configuration:**
  - Sub-Protocol 6A (Replay): 100 games across $N \in \{2, 3, 4, 5, 6\}$.
  - Sub-Protocol 6B (Checkpoint): 100 games tested at checkpoints $k \in \{5, 15, 30\}$.
  - Total Full: 200 tests.

### 10. Seed Protocol
Seeds `60000` to `60000 + N_games - 1`.

### 11. Seat / Start-Player Protocol
Standard baseline setup.

### 12. Data Collected
- Detailed step event logs: Action indices, emitted events (type, player, details), rewards, terminal flags.
- Trajectory SHA-256 digests:
  $$\text{Hash} = \text{SHA256}(\text{json}(\text{events}) \parallel \text{json}(\text{actions}) \parallel \text{json}(\text{rewards}))$$

### 13. Metric Definitions & Mathematical Formulas
- **Event-Level Equivalence:**
  $$T_A \equiv T_B \iff \forall t, \quad a_{A,t} = a_{B,t} \land e_{A,t} = e_{B,t} \land r_{A,t} = r_{B,t}$$
- **Checkpoint Continuation Equivalence:**
  Let $S_k$ be state at step $k$. Run A continues $S_k \to S_T$. Run B restores $\text{restore\_state}(\text{serialize\_state}(S_k))$ and steps to $S'_T$. Equivalence requires $(a_{A,t}, e_{A,t}) = (a_{B,t}, e_{B,t})$ for all $t \ge k$.

### 14. Statistical Summaries
Reproduction Success Rate (must be exactly 100.0%, 0 failures allowed).

### 15. Required Figures
- N/A (Verification and audit experiment).

### 16. Required Tables
- **Table 6:** Reproducibility audit table (Protocol, Tests Run, Identical Matches, Hash Mismatches, RSR %).

### 17. Expected Interpretation
Proves the simulator is completely free of hidden RNG leaks, unseeded dictionary ordering, or non-deterministic state mutations.

### 18. Failure Conditions
Any mismatch in actions, events, rewards, or terminal state ($\text{RSR} < 100\%$).

### 19. Reproducibility Requirements
Strict zero-tolerance verification.

---

# 5. Scientific Integrity & Data Policy

1. **No Data Discarding:** Every seeded run initiated must be retained in raw JSONL telemetry. Long games or unusual draws are empirical phenomena to be analyzed, not filtered.
2. **Confidence Intervals:** Every empirical proportion (win rate, truncation rate) must report 95% Wilson score intervals.
3. **Distribution Honesty:** Game length and hand size are skewed; both parametric (mean, std) and non-parametric (median, IQR) summaries are mandatory.
4. **Information Isolation:** The experiment telemetry wrapper and analysis oracle must never pass unmasked state or opponent cards to agent decision methods.
5. **Simulator Freeze Check:** Automated test asserts zero modifications to `whot_ml/`.
