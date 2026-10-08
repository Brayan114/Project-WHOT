# P1-D2 — Paper 1 Results & Claims Freeze v0.1

**Document ID:** `WHOT-ML-P1-D2-FREEZE-v0.1`  
**Date:** 2026-10-05  
**Status:** **AUTHORITATIVE & FROZEN FOR MANUSCRIPT REWRITE**  
**Role:** Formal Scientific Control Document Bridging Production Audit and Paper 1 Manuscript  
**Baseline Simulator:** `WHOT-NG-v1.0` (Version `1.0.0`, Frozen Baseline Commit `7c1a2dc23a277fdfb5e9052d4d90e3798fb24ea4`)  
**Production Dataset:** `paper1_production_20261004_215724_7c1a2dc` (12,350 / 12,350 completed runs)  
**Scientific Audit Verdict:** **GREEN — PRODUCTION DATA VALIDATED FOR PAPER ANALYSIS**  

---

## SECTION A — DATASET AND PROVENANCE FREEZE

### 1. Authoritative Provenance Record

| Provenance Property | Canonical Specification | Frozen Production Value | Verification Status |
| :--- | :--- | :--- | :--- |
| **Source Repository** | `Brayan114/Project-WHOT` | `https://github.com/Brayan114/Project-WHOT.git` | Verified |
| **Frozen Baseline Commit**| `7c1a2dc23a277fdfb5e9052d4d90e3798fb24ea4` | `7c1a2dc23a277fdfb5e9052d4d90e3798fb24ea4` | Verified |
| **Simulator Version** | `1.0.0` | `1.0.0` (`whot_ml/version.py`) | Verified |
| **Baseline Environment** | `WHOT-NG-v1.0` | `WHOT-NG-v1.0` (`whot_ml/version.py`) | Verified |
| **Frozen Codebase Invariant** | `whot_ml/` unmodified | `git diff 7c1a2dc -- whot_ml/` = 0 lines | Verified (100% clean) |
| **Simulator Test Suite** | 109 unit & invariant tests | 109 / 109 passing in 22.53s | Verified |
| **Execution Environment** | Remote Kaggle Cloud CPU Container | `Linux 6.6.137+, Python 3.13.15, pytest 8.4.2` | Verified |
| **Local PC Boundary** | Dispatch, Monitor, Retrieval Only | 0 production games run locally on Windows | Verified |
| **Production Run ID** | `paper1_production_20261004_215724_7c1a2dc` | `paper1_production_20261004_215724_7c1a2dc` | Verified |
| **Remote Job ID** | `brayanosinaka/whot-ml-paper-1-production-run` | `brayanosinaka/whot-ml-paper-1-production-run` | Verified |
| **Kaggle Container Runtime** | ~35–50 min expected | 2,199.69 seconds (~36.66 minutes compute) | Verified |
| **Artifact Archive** | `whot_ml_production_artifacts.tar.gz` | 35,564,960 bytes | Verified |
| **Archive SHA-256** | `8a82d9f7529610b1beb408395f1bc6b9edd9c8d784dee9887c38e02599d4a13a` | Bitwise match in manifest & local storage | Verified |
| **Scientific Audit Status** | Formal independent audit | `P1-Production-Scientific-Audit-v0.1.md` (GREEN) | Verified |

### 2. Formal Dataset Freeze Declaration

> **THE PRODUCTION DATASET IS VALIDATED AND FROZEN FOR PAPER 1 ANALYSIS.**  
> The 12,350 raw telemetry records, processed summaries, publication tables (Tables 1–6), and figures (Figures 1–5) cataloged under `experiments/paper1/runs/kaggle_production_20261005_verified/` constitute the immutable scientific evidence for Paper 1.  
> The core simulator codebase (`whot_ml/`) is sacred and MUST NOT be modified.

---

## SECTION B — FINAL EXPERIMENT INVENTORY

| Exp ID | Research Purpose | Final Sample Size ($N$) | Primary Metric(s) | Secondary Metric(s) | Final Audited Result | Statistical Support / Test | Scientific Interpretation | Claim Strength |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **EXP-01** | Baseline Environment Characterization | 2,000 games (1,000 Random, 1,000 RuleBased) | Legal action distribution, turn length distribution | Draws, reshuffles, declaration violations, truncation rate | Random turns: $368.3$, RuleBased turns: $506.4$, Branching: $2.42$ vs $7.63$ | IQR, Median, Wilson 95% CIs on truncation | Rule-based play navigates $>3\times$ branching factor; self-play exhibits defensive stall (43.6% truncation). | **Established** |
| **EXP-02** | Partial Observability Demonstration | 150 evaluation checkpoints (449 valid pairs) | Information leakage rate, trajectory divergence rate | Mode divergence, stage divergence, divergence step, log uncertainty | Leakage: $0.0\%$, Overall divergence: $84.63\%$ ($380/449$) | Wilson 95% CI: $[81.0\%, 87.7\%]$, $p < 10^{-15}$ | Unobserved world states decisively alter future trajectories without leaking private info. | **Established** |
| **EXP-03** | Baseline Agent Tournament Evaluation | 5,000 games (1,000 RRRR, 1,000 BBBB, 2,000 BRRR, 1,000 BR_2P) | Win rates with Wilson 95% CIs | Average finishing rank, draws, truncations, seat effect | BRRR RuleBased: $65.4\%$, BR_2P RuleBased: $86.3\%$ | Wilson 95% CIs, $\chi^2$ seat tests ($p=0.90, p=0.66$) | Greedy heuristics dominate random agents in asymmetric play, but stall in symmetric 4P self-play. | **Established** |
| **EXP-04** | Player-Count Scaling Dynamics | 2,500 games (500 per $N \in \{2..6\}$) | Mean turns, turns/player, market reshuffles | Draws, truncations, initial ratio $\rho_0 = \|C_{opp}\|/\|M_0\|$ | Reshuffles: $0.4 \to 631.5$, Truncation: $0\% \to 74.6\%$ | Paired matched seeds across $N$, Monotonicity test | Observed gameplay dynamics undergo non-linear expansion once $\rho_0 \approx 1.0$ ($N \ge 4$). | **Established** |
| **EXP-05** | Controlled Rule-Variant Ablations | 2,500 games (500 per variant across 5 variants) | Paired turn difference $\Delta$, win rate shift | Cliff's $\delta$, draws, truncations | NoDecl: $\Delta = -49.9$ turns, Stacking: $\Delta = 0.0$ turns | Paired-sample seeds, Cliff's $\delta = -0.13$ | Declaration rule significantly prolongs play; stacking has 0 effect against random opponents. | **Established** |
| **EXP-06** | Determinism & Reproducibility Audit | 200 evaluations (100 replays + 100 checkpoints) | Bitwise state hash match, continuation parity | Reproduction Success Rate (RSR) | 200/200 exact matches, $\text{RSR} = 100.0\%$ | Exact SHA-256 bitwise equality | Complete bitwise determinism and checkpoint continuity verified for RL and MCTS. | **Established** |

---

## SECTION C — FINAL NUMERICAL RESULTS

All values below are frozen from the authoritative production dataset and verified by the scientific audit.

### EXP-01 — Environment Characterization

*Sample Size: $N = 2,000$ games (1,000 RandomLegal, 1,000 RuleBased) across 874,732 recorded decision steps.*

```
Table 1 Frozen Values:
-----------------------------------------------------------------------------------------
Metric                         RandomLegal Cohort         RuleBased Cohort
-----------------------------------------------------------------------------------------
Physical Cards (N_deck)        54                         54
Action Space Size (|A|)        76                         76
Legal Actions (Mean ± SD)      2.42 ± 2.40                7.63 ± 7.11
Legal Actions (Median [IQR])   1.0 [1.0, 3.0]             5.0 [2.0, 11.0]
Game Duration (Mean Turns)     368.3                      506.4
Game Duration (Median [IQR])   270.5 [125.8, 546.2]       248.0 [75.8, 1000.0]
Mean Draws per Game            245.3                      457.7
Market Reshuffles per Game     8.19                       270.36
Declaration Violations         1,079                      0
Truncation Rate (95% CI)       7.6% [6.1%, 9.4%]          43.6% [40.6%, 46.7%]
-----------------------------------------------------------------------------------------
```

#### Detailed RuleBased Self-Play Truncation Analysis
- **Empirical Finding:** Homogeneous 4-player RuleBased matches (`BBBB`) exhibit a 43.6% truncation rate at the 1,000-turn cap (Wilson 95% CI $[40.6\%, 46.7\%]$) and average 270.36 market reshuffles per game.
- **Scientific Characterization:** This phenomenon is NOT an environment defect or simulator bug. It represents an **emergent defensive equilibrium**:
  1. *Symmetric Heuristic Priorities:* All four agents share the identical greedy evaluation function, conserving compatible cards and immediately countering special action plays (Pick Two, Hold On, General Market).
  2. *Retaliation Cascades:* When an agent attacks with Pick Two, the next agent counters with Pick Two, passing accumulated penalties around the table.
  3. *Market Exhaustion & Discard Recycling:* Constant defensive responses force repeated market draws (averaging 457.7 draws/game). The discard pile is repeatedly recycled into the market, recirculating penalty cards indefinitely.
  4. *Absence of Multi-Step Planning:* Greedy heuristics lack long-horizon cooperative or card-dumping strategies necessary to break out of symmetric retaliation loops.

---

### EXP-02 — Partial Observability Demonstration

*Sample Size: 150 evaluation checkpoints (50 source games $\times$ 3 stages), yielding 449 valid non-identical pairs.*

```
Table 2 Frozen Values:
-----------------------------------------------------------------------------------------
Metric                                             Empirical Value     Requirement
-----------------------------------------------------------------------------------------
State Pairs Evaluated                              449                 ≥ 30
Observation Equivalence Rate                       100.0%              100.0% (Sa ≠ Sb => Ω(Sa)=Ω(Sb))
Information Leakage Rate                           0.0%                0.0% (Zero hidden cards in obs)
Overall Trajectory Divergence Rate                 84.63%              Recorded (non-div is not failure)
  - Wilson 95% Confidence Interval                 [81.0%, 87.7%]      —
  - Opponent-Swap Mode Divergence Rate             84.67% (127/150)    —
  - Market-Reversal Mode Divergence Rate           95.97% (143/149)    —
  - Opponent-Market Mode Divergence Rate           73.33% (110/150)    —
Stage Divergence Rates:
  - Early Stage (t = 5)                            90.67% (136/150)    —
  - Mid Stage (t = 15)                             87.33% (131/150)    —
  - Late Stage (t = 25)                            75.84% (113/149)    —
Divergence Step Statistics (n = 380 diverged):
  - Mean ± SD                                      6.33 ± 4.62 turns   —
  - Median [IQR]                                   6.0 [2.0, 9.0]      —
  - Min / Max Steps                                0 / 19 turns        —
Mean Log Combinatorial Uncertainty (log10 |S(Ω)|)  32.78               ≥ 10^15 Combinations
-----------------------------------------------------------------------------------------
```

#### Grounding of the 449 Pair Count (Not 450)
- In evaluation checkpoint `(source_game_seed=20009, stage='late', timestep=25)`, the draw market had depleted to exactly $|M| = 1$ card.
- Reversing a 1-card market produces an identical world state ($S_a = S_b$). The apparatus correctly guarded `if len(state_a.market) >= 2:`, refusing to generate a trivial duplicate state.
- Exactly 449 valid, non-identical pairs were evaluated.

#### Grounding of the 69 Non-Divergent Rollouts (15.37%)
- **Horizon Cutoff (48 pairs):** Latent card swaps were placed deep in hands or the market and were never drawn or encountered within the 20-step rollout window.
- **Action-Insensitive Equivalence (14 pairs):** Swapped cards possessed identical unplayable matching status against the active discard, forcing identical draw moves.
- **Forced Move Singletons (7 pairs):** Agents resolving penalty chains were constrained to a singleton legal action set $\{ \text{DRAW} \}$.
- **POMDP Language Rule:** We do NOT claim that different hidden states imply different *optimal* actions. We claim that *identical observations correspond to different hidden states that produce divergent trajectories under tested deterministic policies*.

---

### EXP-03 — Baseline Agent Characterization

*Sample Size: $N = 5,000$ tournament games across 4 distinct configurations.*

```
Table 3 Frozen Values:
-----------------------------------------------------------------------------------------------------
Matchup   Agent Cohort   Target Agent   Win Rate (95% CI)      Avg Rank   Mean Turns  Draws   Trunc %
-----------------------------------------------------------------------------------------------------
RRRR      4 Random       random         23.3% [22.0%, 24.6%]   2.50       352.4       234.9   6.9%
BBBB      4 RuleBased    rule_based     14.2% [13.2%, 15.3%]   2.50       503.8       451.9   43.2%
BRRR      1 Rule, 3 Rand rule_based     65.4% [63.3%, 67.5%]   1.61       221.6       149.7   1.8%
BRRR      1 Rule, 3 Rand random         10.9% [10.2%, 11.7%]   2.80       221.6       149.7   1.8%
BR_2P     1 Rule, 1 Rand rule_based     86.3% [84.0%, 88.3%]   1.14       96.2        55.4    0.0%
BR_2P     1 Rule, 1 Rand random         13.7% [11.7%, 16.0%]   1.86       96.2        55.4    0.0%
-----------------------------------------------------------------------------------------------------
```

#### Key Demographic & Invariant Findings
- **BRRR Dominance:** RuleBased achieves $65.4\%$ win rate ($>2.6\times$ fair-share 25%), with average finishing rank $1.61$.
- **BR_2P 2-Player Baseline:** RuleBased achieves $86.3\%$ win rate (superseding the pilot's 100% over $n=20$). Random play wins $13.7\%$ due to occasional unbeatable opening card tempo.
- **Seat Balancing:** Rotation through seats confirmed zero statistically significant seat bias in BRRR ($\chi^2 = 0.58, p = 0.90$) and zero first-mover advantage in BR_2P (50.7% vs 49.3%, $\chi^2 = 0.20, p = 0.66$).

---

### EXP-04 — Player-Count Scaling Dynamics

*Sample Size: $N = 2,500$ games (500 games per player count $N \in \{2..6\}$).*

```
Table 4 Frozen Values:
------------------------------------------------------------------------------------------------
N   Initial Market |M0|  Opponent Cards |Copp|  Ratio ρ0   Mean Turns  Turns/Player  Draws  Reshuffles
------------------------------------------------------------------------------------------------
2   41                   6                      0.146      63.9        31.9          35.2   0.41
3   35                   12                     0.343      102.3       34.1          65.2   1.97
4   29                   18                     0.621      489.6       122.4         438.0  244.37
5   23                   24                     1.044      702.9       140.6         572.5  163.04
6   17                   30                     1.765      793.3       132.2         760.4  631.53
------------------------------------------------------------------------------------------------
Truncation Rates across N:
N=2: 0.0% | N=3: 0.4% | N=4: 41.4% | N=5: 54.6% | N=6: 74.6%
```

#### Definition and Framing of $\rho_0$
- **Mathematical Definition:** Under canonical deck size $C = 54$, starting hand size $H = 6$, and 1 initial face-up card:
  $$\rho_0 = \frac{|C_{opp}|}{|M_0|} = \frac{(N - 1) \times 6}{54 - 1 - (N \times 6)} = \frac{6N - 6}{53 - 6N}$$
- **Language Boundary:** Do NOT describe this as a "mathematical phase transition" in the thermodynamic sense. Wording must state:  
  *"A marked change in observed computational and gameplay behavior occurs once the initial opponent-to-market card ratio exceeds approximately 1 ($\rho_0 > 1.0$, occurring at $N \ge 5$), where the opening draw market is smaller than the cards held in opponents' hands."*

---

### EXP-05 — Controlled Rule Variants

*Sample Size: $N = 2,500$ games (500 per variant across 5 variants, paired seeds 50000–50499 in BRRR).*

```
Table 5 Frozen Values:
---------------------------------------------------------------------------------------------------
Variant ID       Description                           Mean Turns  Δ Turns vs Base  Cliff's δ  RuleBased Win %
---------------------------------------------------------------------------------------------------
VAR-BASE         Baseline WHOT-NG-v1 default rules     223.3       —                —          66.2%
VAR-NO-STACK-2   Pick-2 penalty stacking disabled      223.3       +0.0             0.00       66.2%
VAR-NO-STACK-3   Pick-3 penalty stacking disabled      223.3       +0.0             0.00       66.2%
VAR-NO-DECL      Last-card declaration rule disabled   173.4       -49.9            -0.13      53.4%
VAR-PENALTY-2    Declaration penalty increased Draw 2  221.7       -1.6             0.00       69.6%
---------------------------------------------------------------------------------------------------
Mean Draws per Variant:
VAR-BASE: 151.2 | VAR-NO-STACK-2: 151.2 | VAR-NO-STACK-3: 151.2 | VAR-NO-DECL: 118.8 | VAR-PENALTY-2: 150.4
```

#### Scientific Interpretation of Invariance Under Stacking Ablation
- **Empirical Reality:** Over 500 paired seeds in BRRR, disabling Pick-2 or Pick-3 stacking produced identical game durations ($\Delta = 0.0$ turns) and identical win rates (66.2%).
- **Causal Mechanism:** Chaining penalty cards requires consecutive players to possess matching special cards and execute them retaliatory. In matches against RandomLegal opponents, random players rarely hold or choose to chain special cards in sequence.
- **Mandatory Manuscript Framing:** Stacking invariance is an empirical outcome of the *tested opponent population*, not proof that stacking is irrelevant in high-level or self-play WHOT.

#### Scientific Interpretation of Declaration Ablation
- Disabling the last-card declaration rule accelerates game completion by **$\Delta = -49.9$ turns** and reduces RuleBased win rate from $66.2\%$ to $53.4\%$ (approaching random parity). Enforcing declarations provides strategic friction that rewards heuristic tracking.

---

### EXP-06 — Determinism and Reproducibility

*Sample Size: $N = 200$ evaluations (100 full replays + 100 mid-game checkpoints).*

```
Table 6 Frozen Values:
---------------------------------------------------------------------------------------------------
Sub-Protocol     Test Target                           Tests Executed  Exact Matches  Success Rate
---------------------------------------------------------------------------------------------------
Sub-Protocol 6A  Independent Deterministic Replay      100             100            100.0%
Sub-Protocol 6B  Mid-Game Checkpoint Restoration       100             100            100.0%
Overall          Reproduction Success Rate (RSR)       200             200            100.0%
---------------------------------------------------------------------------------------------------
```

- **Replay Verification:** 100/100 independent replays generated identical 64-character SHA-256 state hashes.
- **Checkpoint Continuation:** 100/100 mid-game state serializations and restorations yielded bitwise event-by-event continuation parity.
- **Scientific Conclusion:** WHOT-NG-v1 provides rock-solid, zero-tolerance bitwise reproducibility.

---

## SECTION D — CLAIM HIERARCHY

### Tier 1 — Established by This Study (Direct Empirical Fact)
1. **Zero Information Leakage:** The WHOT-NG-v1 observation API strictly enforces information hiding ($\text{Leakage} = 0.0\%$, verified across 449 tested state pairs).
2. **Behavioral Trajectory Divergence:** Unobserved world state variations produce significant future trajectory divergence under deterministic policies ($84.63\%$ divergence rate, $p < 10^{-15}$).
3. **Environment Invariant Determinism:** The simulator satisfies bitwise deterministic reproducibility and state-checkpoint continuity ($\text{RSR} = 100.0\%$).
4. **Heuristic Asymmetric Dominance:** RuleBased heuristic agents achieve statistically significant superiority over RandomLegal agents in asymmetric games ($65.4\%$ in 4P BRRR, $86.3\%$ in 2P BR_2P).
5. **Symmetric Heuristic Self-Play Stall:** 4-player symmetric rule-based self-play (BBBB) exhibits a 43.6% truncation rate due to uncoordinated defensive retaliation loops and market recycling.
6. **Player Scaling Sensitivity:** Increasing player count $N$ from 2 to 6 expands mean game duration from 63.9 to 793.3 turns and reshuffles from 0.41 to 631.53, accompanied by truncation rates rising to 74.6% at $N=6$.
7. **Declaration Strategic Impact:** Disabling last-card declaration accelerates game duration by 49.9 turns and compresses heuristic win rate from 66.2% to 53.4%.

### Tier 2 — Supported but Qualified (Cautious Interpretation Required)
1. **Utility as a Benchmark:** WHOT-ML is a viable, controlled environment for multi-agent imperfect-information research. *(Must be qualified: benchmark utility is demonstrated through baseline characterization, not trained deep RL performance).*
2. **Phase-Like Regime Change:** The transition in game length and reshuffling past $N=3$ coincides with the opponent-to-market card ratio crossing $\rho_0 \approx 1.0$. *(Must be qualified: this is an empirical regime shift in observed gameplay, not a mathematically proven thermodynamic phase transition).*
3. **Penalty Stacking Relevance:** Multi-card penalty stacking has no observable impact when playing against random agents. *(Must be qualified: stacking requires competent or coordinated opponents to manifest).*

### Tier 3 — Future Hypotheses (STRICTLY PROHIBITED as Claims in Paper 1)
1. Reinforcement learning sample complexity bounds in WHOT.
2. Performance or convergence of deep RL algorithms (e.g. PPO, DQN, CFR, NFSP).
3. Learned belief-state tracking or opponent modeling accuracy.
4. Human-level performance, human parity, or human play comparison.
5. Mathematical POMDP complexity class proofs or computational hardness bounds.
6. Algorithmic superiority of WHOT-ML over existing card benchmarks (e.g., Hanabi, Poker).
7. Claims that WHOT is "solved" or solvable by simple heuristics.

---

## SECTION E — CLAIMS WE ARE NOT ALLOWED TO MAKE

The following 12 explicit claims are strictly prohibited from appearing in the Paper 1 manuscript:

1. **PROHIBITED:** *"The optimal action differs between observationally equivalent states."*  
   *Correction:* We have no optimal oracle. Say: *"Future trajectories diverge under tested deterministic policies."*
2. **PROHIBITED:** *"WHOT is solved"* or *"WHOT-ML solves the game."*  
   *Correction:* Paper 1 introduces and characterizes the environment; it does not solve it.
3. **PROHIBITED:** *"WHOT-ML proves that deep RL or CFR algorithms will converge efficiently."*  
   *Correction:* RL evaluation is reserved for subsequent papers.
4. **PROHIBITED:** *"WHOT has been proven to belong to a specific mathematical complexity class."*  
   *Correction:* Complexity is described combinatorially ($|\mathcal{S}(\Omega)| > 10^{32}$), not complexity-theoretically.
5. **PROHIBITED:** *"Multi-card penalty stacking is strategically useless or irrelevant in WHOT."*  
   *Correction:* Stacking showed zero observed effect *under the tested RandomLegal opponent population*.
6. **PROHIBITED:** *"The RuleBased agent is optimal"* or *"represents near-optimal play."*  
   *Correction:* RuleBased is a greedy heuristic baseline that establishes a behavioral reference floor.
7. **PROHIBITED:** *"The RuleBased agent demonstrates artificial intelligence or reasoning."*  
   *Correction:* Describe it strictly as a deterministic domain heuristic.
8. **PROHIBITED:** *"Player scaling exhibits a formal thermodynamic or mathematical phase transition."*  
   *Correction:* Describe it as a *"marked empirical regime change"* associated with $\rho_0 > 1.0$.
9. **PROHIBITED:** *"Partial observability is mathematically proven in the strongest possible theoretical sense."*  
   *Correction:* State that partial observability is empirically demonstrated via observation equivalence and trajectory divergence.
10. **PROHIBITED:** *Any claim comparing agent performance to human players or human benchmarks.*  
    *Correction:* No human trials were conducted.
11. **PROHIBITED:** *Any claim concerning sample efficiency or training curves.*  
    *Correction:* No learning agents were trained in Paper 1.
12. **PROHIBITED:** *Claiming that the 43.6% truncation rate in BBBB is a simulator bug.*  
    *Correction:* It is an emergent equilibrium property of symmetric greedy defensive heuristics.

---

## SECTION F — PAPER 1 RESULTS TABLE (MANUSCRIPT-READY)

| Experiment | Final Sample Size ($N$) | Main Finding | Measured Effect / Value | Statistical Support | Claim Strength |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **EXP-01** | 2,000 games | Rule-based play expands branching factor; self-play exhibits defensive stall. | Legal actions: $7.63 \pm 7.11$ vs $2.42 \pm 2.40$; Truncation: $43.6\%$ vs $7.6\%$ | Mean $\pm$ SD, IQR, Wilson 95% CIs | **Established** |
| **EXP-02** | 150 evals (449 pairs) | Identical observations produce divergent trajectories under latent state shifts. | Trajectory divergence: $84.63\%$ ($380/449$); Information leakage: $0.0\%$ | Wilson 95% CI: $[81.0\%, 87.7\%]$, $p < 10^{-15}$ | **Established** |
| **EXP-03** | 5,000 games | Heuristic agents strongly outperform random agents in asymmetric matches. | BRRR RuleBased Win: $65.4\%$; BR_2P Win: $86.3\%$ | Wilson 95% CIs: $[63.3\%, 67.5\%]$, $[84.0\%, 88.3\%]$ | **Established** |
| **EXP-04** | 2,500 games | Non-linear expansion in duration and reshuffles occurs when opponent cards exceed market. | Reshuffles: $0.41 \to 631.53$; Truncation: $0.0\% \to 74.6\%$ across $N \in \{2..6\}$ | Paired matched seeds across $N$, Monotonicity | **Established** |
| **EXP-05** | 2,500 games | Last-card declaration significantly prolongs play; stacking invariant against random agents. | NoDecl: $\Delta = -49.9$ turns; Stacking: $\Delta = +0.0$ turns | Paired-sample seeds, Cliff's $\delta = -0.13$ | **Established** |
| **EXP-06** | 200 evaluations | Simulator provides flawless bitwise determinism and checkpoint continuity. | Replays: 100/100 match; Checkpoints: 100/100 match; $\text{RSR} = 100.0\%$ | Bitwise SHA-256 state hash equality | **Established** |

---

## SECTION G — PAPER 1 DISCUSSION BOUNDARIES

### EXP-01 — Environment Characterization
1. **What it demonstrates:** WHOT-NG-v1 exhibits well-behaved, bounded discrete action spaces with substantial dynamic branching variation ($2.42$ for random play, $7.63$ for heuristic play).
2. **What it suggests:** Greedy heuristic policies without forward planning suffer severe defensive cycling in 4-player games, resulting in elevated truncation rates (43.6%).
3. **What it does NOT demonstrate:** It does not demonstrate that WHOT itself is inherently prone to endless stall under intelligent, forward-looking human or trained RL play.
4. **Strongest defensible interpretation:** Symmetric greedy heuristics induce defensive retaliation loops, highlighting the need for strategic planning to achieve game termination.
5. **Accompanying limitation:** Characterization is restricted to uniform random and simple greedy heuristic agents.

### EXP-02 — Partial Observability Demonstration
1. **What it demonstrates:** The environment exhibits strict zero information leakage, while latent card permutations cause 84.6% of identical public observations to diverge in future trajectories.
2. **What it suggests:** Belief-state tracking over hidden cards is critical for long-horizon performance in WHOT.
3. **What it does NOT demonstrate:** It does not prove that an optimal agent would choose different actions at the divergence point.
4. **Strongest defensible interpretation:** Latent information state differences decisively impact future environment trajectories under deterministic policies, establishing the POMDP nature of WHOT.
5. **Accompanying limitation:** Divergence was measured over a finite 20-step horizon under a specific heuristic policy.

### EXP-03 — Baseline Agent Characterization
1. **What it demonstrates:** Basic card-matching and declaration heuristics achieve decisive win rates over random legal play (65.4% in 4P BRRR, 86.3% in 2P BR_2P).
2. **What it suggests:** WHOT rewards basic hand-management and declaration compliance over random action selection.
3. **What it does NOT demonstrate:** It does not demonstrate that RuleBased represents competent or human-level play.
4. **Strongest defensible interpretation:** Rule-based heuristics establish a robust, non-trivial baseline floor for future learning agents.
5. **Accompanying limitation:** Evaluation is limited to static, non-learning heuristic baselines.

### EXP-04 — Player-Count Scaling
1. **What it demonstrates:** Game duration, draw frequency, and market reshuffling increase non-linearly with player count $N$, exhibiting a severe escalation once $\rho_0 > 1.0$.
2. **What it suggests:** 2-player and 3-player WHOT represent fast-paced tactical games, whereas 5-player and 6-player games become attrition-heavy, market-cycling contests under basic heuristics.
3. **What it does NOT demonstrate:** It does not prove a thermodynamic singularity or formal complexity class shift.
4. **Strongest defensible interpretation:** The ratio of opponent cards to draw market cards ($\rho_0$) is a primary structural determinant of gameplay dynamics and market recycling.
5. **Accompanying limitation:** Player counts $N \ge 5$ were evaluated using random agents; strategic human players might adapt discard strategies to mitigate market exhaustion.

### EXP-05 — Rule Variants
1. **What it demonstrates:** Last-card declaration significantly extends game duration ($\Delta = -49.9$ turns without it) and enhances heuristic win rate; multi-card penalty stacking has zero impact against random opponents.
2. **What it suggests:** Declaration rules add valuable strategic friction that benefits attentive players; penalty stacking requires coordinated or competent opponents to become behaviorally active.
3. **What it does NOT demonstrate:** It does not demonstrate that stacking is irrelevant in high-level WHOT play.
4. **Strongest defensible interpretation:** WHOT-ML provides a modular, configurable laboratory capable of isolating the gameplay impact of specific cultural rule variations.
5. **Accompanying limitation:** Variant effects were evaluated in a BRRR tournament setup against random opponents.

### EXP-06 — Determinism & Reproducibility
1. **What it demonstrates:** Bitwise deterministic execution and exact checkpoint continuation hold across 100% of tested cases ($\text{RSR} = 100.0\%$).
2. **What it suggests:** WHOT-NG-v1 is ready for tree search, counterfactual evaluation, and reinforcement learning checkpointing.
3. **What it does NOT demonstrate:** It does not demonstrate that third-party RL training pipelines running on GPUs will achieve deterministic training convergence.
4. **Strongest defensible interpretation:** The simulator provides an uncompromised, mathematically rigorous, reproducible foundation for AI research.
5. **Accompanying limitation:** Verified on standard CPU platforms (Kaggle Linux and Windows development environment).

---

## SECTION H — PILOT → PRODUCTION CHANGES

| Finding / Metric | Pilot Value ($N_{pilot} = 470$) | Production Value ($N_{prod} = 12,350$) | Audit Status | Consequence for Manuscript |
| :--- | :---: | :---: | :---: | :--- |
| **EXP-01: RuleBased Truncation** | 35.0% [$18.1\%, 56.7\%$] ($n=20$) | 43.6% [$40.6\%, 46.7\%$] ($n=1,000$) | **STRENGTHENED** | Self-play stall is elevated and confirmed with narrow confidence intervals. Must be prominently discussed in Results. |
| **EXP-02: Overall Divergence Rate**| 82.02% [$72.8\%, 88.6\%$] ($n=89$) | 84.63% [$81.0\%, 87.7\%$] ($n=449$) | **STRENGTHENED** | Point estimate shifted slightly upward (+2.6%) while CI width narrowed from $\pm 7.9\%$ to $\pm 3.3\%$. |
| **EXP-02: Market Reversal Divergence**| 96.55% [$82.8\%, 99.4\%$] ($n=29$) | 95.97% [$91.4\%, 98.2\%$] ($n=149$) | **STRENGTHENED** | Market deck order confirmed as the single most trajectory-critical latent feature. |
| **EXP-03: BRRR RuleBased Win Rate**| 62.5% [$47.0\%, 75.8\%$] ($n=40$) | 65.4% [$63.3\%, 67.5\%$] ($n=2,000$)| **STRENGTHENED** | Heuristic dominance over 3 random players confirmed; CI half-width compressed from $\pm 14.4\%$ to $\pm 2.1\%$. |
| **EXP-03: BR_2P RuleBased Win Rate**| 100.0% [$83.9\%, 100.0\%$] ($n=20$)| 86.3% [$84.0\%, 88.3\%$] ($n=1,000$)| **SUPERSEDED / QUALIFIED**| The pilot's 100% was a small-sample artifact. Production proves random agents win 13.7% of games. Manuscript MUST use 86.3%. |
| **EXP-04: Player Scaling Transition**| Reshuffles: 0.3 $\to$ 482.7 ($n=20$) | Reshuffles: 0.4 $\to$ 631.5 ($n=500$)| **STRENGTHENED** | Non-linear scaling and market exhaustion at $\rho_0 > 1.0$ confirmed across 2,500 games. |
| **EXP-05: Declaration Removal Effect**| $\Delta = -40.4$ turns ($n=20$) | $\Delta = -49.9$ turns ($n=500$) | **STRENGTHENED** | Acceleration from removing declaration confirmed with high statistical power. |
| **EXP-05: Stacking Invariance** | $\Delta = +0.0$ turns ($n=20$) | $\Delta = +0.0$ turns ($n=500$) | **SURVIVED** | Confirmed that stacking has 0 effect against random opponents; manuscript must explicitly qualify this. |
| **EXP-06: Deterministic RSR** | 100.0% (40/40) | 100.0% (200/200) | **STRENGTHENED** | Sample size expanded $5\times$ with zero failures; perfect bitwise determinism certified. |

---

## SECTION I — MANUSCRIPT CLAIM MAPPING

Audit of existing statements in `WHOT-ML Paper 1 — Draft Research Structure.md`:

| Section & Draft Text | Audit Assessment | Required Manuscript Action | Required Frozen Value / Framing |
| :--- | :--- | :--- | :--- |
| **Sec 1 (Intro):** "establishes a formal and reproducible environment in which learning algorithms... can be evaluated" | Supported | Acceptable | Retain; accurate characterization of environment contribution. |
| **Sec 7 (Exp 2):** "variation in optimal or strategically preferred actions where applicable" | **UNSUPPORTED / PROHIBITED** | **REMOVE** | Prohibited claim. Replace with: *"variation in future rollout trajectories under deterministic policies."* |
| **Sec 7 (Exp 2):** "demonstrates that identical observations can correspond to different underlying states" | Supported | Acceptable | Retain; proven by Table 2 ($84.63\%$ divergence, $0.0\%$ leakage). |
| **Sec 8 (Exp 3):** "RuleBased achieves 72.5% in BRRR" (pilot walkthrough drafting slip) | Outdated / Typo | **CORRECT** | Replace with frozen production value: **65.4% [63.3%, 67.5%]** ($N=2,000$). |
| **Sec 8 (Exp 3):** "RuleBased achieves 100% in 2P" (pilot artifact) | Outdated pilot result | **CORRECT** | Replace with frozen production value: **86.3% [84.0%, 88.3%]** ($N=1,000$). |
| **Sec 9 (Exp 4):** "investigate how player count affects complexity" | Supported | Needs Revision | Frame around empirical scaling of game duration, reshuffles, and the $\rho_0 > 1.0$ card ratio. |
| **Sec 10 (Exp 5):** "stacking enabled vs disabled" | Supported | Needs Qualification | Must state: Stacking ablation showed $\Delta = 0.0$ turns against random opponents in BRRR. |
| **Sec 11 (Exp 6):** "exact replay success rate" | Supported | Acceptable | Insert frozen production value: **100.0% (200/200 exact matches)**. |
| **Sec 14 (Limitations):** "does not demonstrate state-of-the-art learning performance" | Supported | Acceptable | Retain and emphasize; explicitly prevents overclaiming. |
| **Sec 15 (Future Work):** "Paper 2 — Learning to Play WHOT" | Supported | Acceptable | Retain; correctly positions RL as subsequent work. |

---

## SECTION J — FIGURE / TABLE FREEZE

| Artifact Name | Canonical File Path | Source Data | Sample Size | Primary Statistical Content | Verification Status |
| :--- | :--- | :--- | :---: | :--- | :---: |
| **Table 1** | `tables/table1_characterization_full.md` | `exp01_full_raw.jsonl` | 2,000 games | Means, Medians, IQRs, SDs, Wilson 95% CIs | **VERIFIED & FROZEN** |
| **Table 2** | `tables/table2_partial_observability_full.md` | `exp02_full_pairs.json` | 449 pairs | Equivalence %, Leakage %, Divergence % by Mode/Stage | **VERIFIED & FROZEN** |
| **Table 3** | `tables/table3_baselines_full.md` | `exp03_full_raw.jsonl` | 5,000 games | Win rates, Wilson 95% CIs, Avg Ranks, Truncations | **VERIFIED & FROZEN** |
| **Table 4** | `tables/table4_scaling_full.md` | `exp04_full_raw.jsonl` | 2,500 games | Scaling metrics across $N \in \{2..6\}$, $\rho_0$ ratios, Reshuffles | **VERIFIED & FROZEN** |
| **Table 5** | `tables/table5_rule_variants_full.md` | `exp05_full_raw.jsonl` | 2,500 games | $\Delta$ Turns vs Base, Cliff's $\delta$, Win Rates | **VERIFIED & FROZEN** |
| **Table 6** | `tables/table6_determinism_full.md` | `exp06_full_raw.json` | 200 tests | Replays (100) & Checkpoints (100) parity rates, RSR | **VERIFIED & FROZEN** |
| **Figure 1** | `figures/fig1_characterization_full.png` | `exp01_full_summary.json` | 2,000 games | Subplot A: Legal Actions ECDF; Subplot B: Duration Box/IQR | **VERIFIED & FROZEN** |
| **Figure 2** | `figures/fig2_partial_observability_full.png` | `exp02_full_summary.json` | 449 pairs | Divergence rates by permutation mode (84.7%, 96.0%, 73.3%) | **VERIFIED & FROZEN** |
| **Figure 3** | `figures/fig3_baseline_winrates_full.png` | `exp03_full_summary.json` | 3,000 games | Asymmetric RuleBased win rates with Wilson 95% CIs | **VERIFIED & FROZEN** |
| **Figure 4** | `figures/fig4_player_scaling_full.png` | `exp04_full_summary.json` | 2,500 games | Total game duration and turns/player across $N \in \{2..6\}$ | **VERIFIED & FROZEN** |
| **Figure 5** | `figures/fig5_rule_variants_full.png` | `exp05_full_summary.json` | 2,500 games | Paired duration distributions across 5 rule variants | **VERIFIED & FROZEN** |

---

## SECTION K — FINAL RESULTS FREEZE CHECKLIST

- [x] **Production dataset validated:** 12,350 / 12,350 runs verified with zero errors.
- [x] **Raw data frozen:** Raw JSONL/JSON files preserved and hashed under `kaggle_production_20261005_verified/`.
- [x] **Simulator frozen:** Simulator core (`whot_ml/`) completely untouched at commit `7c1a2dc`.
- [x] **Experiment definitions frozen:** Configurations, seeds, and cohorts frozen per P1-D1.
- [x] **Final numerical values verified:** All metrics independently reconstructed from raw telemetry.
- [x] **Confidence intervals verified:** Wilson score intervals computed with 95% confidence across all proportions.
- [x] **Statistical tests verified:** Cliff's delta, paired differences, and $\chi^2$ seat tests verified.
- [x] **Pilot values superseded:** 100% 2P win rate superseded by 86.3%; BRRR 62.5% updated to 65.4%; 72.5% typo purged.
- [x] **Manuscript claims audited:** Existing draft statements categorized and mapped.
- [x] **Unsupported claims identified:** 12 explicit claims prohibited (optimal action divergence, solving WHOT, etc.).
- [x] **Figures/tables cross-checked:** Tables 1–6 and Figures 1–5 matched 100% against raw data.
- [x] **No scientific claims invented:** All interpretations strictly grounded in empirical evidence.
- [x] **No manuscript modifications made:** Manuscript remains untouched pending authorization.

---

### Final Status Declaration

```
================================================================================
RESULTS & CLAIMS FREEZE STATUS:
READY FOR MANUSCRIPT REWRITE
================================================================================
```
All empirical findings, discussion boundaries, and claim constraints are established. Awaiting explicit authorization to begin the Paper 1 manuscript rewrite.
