# P1-Manuscript-Scientific-Audit v0.1

**Document ID:** `WHOT-ML-P1-MANUSCRIPT-AUDIT-v0.1`  
**Date:** 2026-10-05  
**Audit Target:** `WHOT-ML Paper 1 — Manuscript v1.0.md`  
**Baseline Commit:** `7c1a2dc23a277fdfb5e9052d4d90e3798fb24ea4` (100% Frozen Baseline)  
**Production Dataset:** `paper1_production_20261004_215724_7c1a2dc` ($N = 12,350$ Completed Runs)  
**Authority Reference:** `P1-D2 — Paper 1 Results & Claims Freeze v0.1.md`  

---

## 1. Executive Summary & Verdict

This post-rewrite scientific audit was conducted on the complete text of **`WHOT-ML Paper 1 — Manuscript v1.0.md`**. The manuscript was audited against the frozen production evidence, mathematical definitions, claim hierarchies, and prohibited claim boundaries established in **P1-D2**.

```
================================================================================
MANUSCRIPT SCIENTIFIC AUDIT VERDICT:
MANUSCRIPT READY FOR HUMAN REVIEW
================================================================================
```

### Key Verification Metrics
- **Total Numerical Claims Verified:** 58 / 58 (100.0% match with frozen production data)
- **Stale Pilot Numbers Remaining:** 0
- **Prohibited Claims Remaining:** 0
- **Citations Audited:** 16 / 16 verified authentic
- **Simulator Codebase Integrity:** 100% frozen (`git diff 7c1a2dc -- whot_ml/` is empty)
- **Production Dataset Integrity:** Unmodified (SHA-256: `8a82d9f7529610b1beb408395f1bc6b9edd9c8d784dee9887c38e02599d4a13a`)
- **Total Word Count:** 5,142 words (comprehensive research paper length)

---

## 2. Numerical Audit: Raw Telemetry vs. Manuscript Values

Every quantitative metric appearing in `WHOT-ML Paper 1 — Manuscript v1.0.md` was cross-checked against the raw production calculations and frozen P1-D2 tables:

| Experiment | Metric Name | Raw Production Value | P1-D2 Frozen Value | Manuscript v1.0 Value | Audit Match |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **EXP-01** | Total games evaluated | 2,000 | 2,000 | 2,000 | **MATCH** |
| **EXP-01** | Total steps logged | 874,732 | 874,732 | 874,732 | **MATCH** |
| **EXP-01** | RandomLegal legal actions | $2.42 \pm 2.40$ | $2.42 \pm 2.40$ | $2.42 \pm 2.40$ | **MATCH** |
| **EXP-01** | RuleBased legal actions | $7.63 \pm 7.11$ | $7.63 \pm 7.11$ | $7.63 \pm 7.11$ | **MATCH** |
| **EXP-01** | RandomLegal duration mean | 368.3 turns | 368.3 turns | 368.3 turns | **MATCH** |
| **EXP-01** | RuleBased duration mean | 506.4 turns | 506.4 turns | 506.4 turns | **MATCH** |
| **EXP-01** | RandomLegal median duration | 270.5 [125.8, 546.2] | 270.5 [125.8, 546.2] | 270.5 [125.8, 546.2] | **MATCH** |
| **EXP-01** | RuleBased median duration | 248.0 [75.8, 1000.0] | 248.0 [75.8, 1000.0] | 248.0 [75.8, 1000.0] | **MATCH** |
| **EXP-01** | RandomLegal draws | 245.3 | 245.3 | 245.3 | **MATCH** |
| **EXP-01** | RuleBased draws | 457.7 | 457.7 | 457.7 | **MATCH** |
| **EXP-01** | RandomLegal reshuffles | 8.19 | 8.19 | 8.19 | **MATCH** |
| **EXP-01** | RuleBased reshuffles | 270.36 | 270.36 | 270.36 | **MATCH** |
| **EXP-01** | Declaration violations | 1,079 (Rand) / 0 (Rule) | 1,079 / 0 | 1,079 / 0 | **MATCH** |
| **EXP-01** | Random truncation rate | 7.6% [6.1%, 9.4%] | 7.6% [6.1%, 9.4%] | 7.6% [6.1%, 9.4%] | **MATCH** |
| **EXP-01** | RuleBased truncation rate | 43.6% [40.6%, 46.7%] | 43.6% [40.6%, 46.7%] | 43.6% [40.6%, 46.7%] | **MATCH** |
| **EXP-02** | Valid pairs evaluated | 449 | 449 | 449 | **MATCH** |
| **EXP-02** | Observation equivalence % | 100.0% | 100.0% | 100.0% | **MATCH** |
| **EXP-02** | Information leakage % | 0.0% | 0.0% | 0.0% | **MATCH** |
| **EXP-02** | Overall trajectory divergence | 84.63% (380/449) | 84.63% | 84.63% | **MATCH** |
| **EXP-02** | Divergence 95% Wilson CI | [81.0%, 87.7%] | [81.0%, 87.7%] | [81.0%, 87.7%] | **MATCH** |
| **EXP-02** | Opponent-Swap divergence | 84.67% (127/150) | 84.67% | 84.67% | **MATCH** |
| **EXP-02** | Market-Reversal divergence | 95.97% (143/149) | 95.97% | 95.97% | **MATCH** |
| **EXP-02** | Opponent-Market divergence | 73.33% (110/150) | 73.33% | 73.33% | **MATCH** |
| **EXP-02** | Early stage divergence | 90.67% (136/150) | 90.67% | 90.67% | **MATCH** |
| **EXP-02** | Mid stage divergence | 87.33% (131/150) | 87.33% | 87.33% | **MATCH** |
| **EXP-02** | Late stage divergence | 75.84% (113/149) | 75.84% | 75.84% | **MATCH** |
| **EXP-02** | Divergence step mean $\pm$ SD | $6.33 \pm 4.62$ | $6.33 \pm 4.62$ | $6.33 \pm 4.62$ | **MATCH** |
| **EXP-02** | Divergence step median [IQR] | 6.0 [2.0, 9.0] | 6.0 [2.0, 9.0] | 6.0 [2.0, 9.0] | **MATCH** |
| **EXP-02** | Mean log combinatorial uncert | 32.78 | 32.78 | 32.78 | **MATCH** |
| **EXP-02** | Non-divergent rollouts count | 69 (15.37%) | 69 (15.37%) | 69 (15.37%) | **MATCH** |
| **EXP-02** | Horizon cutoff cases | 48 | 48 | 48 | **MATCH** |
| **EXP-02** | Playability insensitivity cases| 14 | 14 | 14 | **MATCH** |
| **EXP-02** | Forced singleton draw cases | 7 | 7 | 7 | **MATCH** |
| **EXP-03** | RRRR Random win rate | 23.3% [22.0%, 24.6%] | 23.3% [22.0%, 24.6%] | 23.3% [22.0%, 24.6%] | **MATCH** |
| **EXP-03** | BBBB RuleBased win rate | 14.2% [13.2%, 15.3%] | 14.2% [13.2%, 15.3%] | 14.2% [13.2%, 15.3%] | **MATCH** |
| **EXP-03** | BBBB truncation rate | 43.2% | 43.2% | 43.2% | **MATCH** |
| **EXP-03** | BRRR RuleBased win rate | 65.4% [63.3%, 67.5%] | 65.4% [63.3%, 67.5%] | 65.4% [63.3%, 67.5%] | **MATCH** |
| **EXP-03** | BRRR RuleBased avg rank | 1.61 | 1.61 | 1.61 | **MATCH** |
| **EXP-03** | BRRR Random win rate | 10.9% [10.2%, 11.7%] | 10.9% [10.2%, 11.7%] | 10.9% [10.2%, 11.7%] | **MATCH** |
| **EXP-03** | BR_2P RuleBased win rate | 86.3% [84.0%, 88.3%] | 86.3% [84.0%, 88.3%] | 86.3% [84.0%, 88.3%] | **MATCH** |
| **EXP-03** | BR_2P Random win rate | 13.7% [11.7%, 16.0%] | 13.7% [11.7%, 16.0%] | 13.7% [11.7%, 16.0%] | **MATCH** |
| **EXP-03** | BRRR Seat effect $\chi^2, p$ | $\chi^2 = 0.58, p = 0.90$ | $\chi^2 = 0.58, p = 0.90$ | $\chi^2 = 0.58, p = 0.90$ | **MATCH** |
| **EXP-03** | BR_2P Starter $\chi^2, p$ | $\chi^2 = 0.20, p = 0.66$ | $\chi^2 = 0.20, p = 0.66$ | $\chi^2 = 0.20, p = 0.66$ | **MATCH** |
| **EXP-04** | $N=2$: Turns / Reshuffles | 63.9 / 0.41 | 63.9 / 0.41 | 63.9 / 0.41 | **MATCH** |
| **EXP-04** | $N=3$: Turns / Reshuffles | 102.3 / 1.97 | 102.3 / 1.97 | 102.3 / 1.97 | **MATCH** |
| **EXP-04** | $N=4$: Turns / Reshuffles | 489.6 / 244.37 | 489.6 / 244.37 | 489.6 / 244.37 | **MATCH** |
| **EXP-04** | $N=5$: Turns / Reshuffles | 702.9 / 163.04 | 702.9 / 163.04 | 702.9 / 163.04 | **MATCH** |
| **EXP-04** | $N=6$: Turns / Reshuffles | 793.3 / 631.53 | 793.3 / 631.53 | 793.3 / 631.53 | **MATCH** |
| **EXP-04** | $\rho_0$ for $N \in \{2..6\}$ | 0.146, 0.343, 0.621, 1.044, 1.765 | Same | Same | **MATCH** |
| **EXP-04** | Truncation across $N$ | 0.0%, 0.4%, 41.4%, 54.6%, 74.6% | Same | Same | **MATCH** |
| **EXP-05** | VAR-BASE Mean turns | 223.3 | 223.3 | 223.3 | **MATCH** |
| **EXP-05** | VAR-NO-STACK-2 $\Delta$ turns | +0.0 | +0.0 | +0.0 | **MATCH** |
| **EXP-05** | VAR-NO-STACK-3 $\Delta$ turns | +0.0 | +0.0 | +0.0 | **MATCH** |
| **EXP-05** | VAR-NO-DECL $\Delta$ turns | -49.9 | -49.9 | -49.9 | **MATCH** |
| **EXP-05** | VAR-NO-DECL Cliff's $\delta$ | -0.13 | -0.13 | -0.13 | **MATCH** |
| **EXP-05** | VAR-NO-DECL Win rate | 53.4% | 53.4% | 53.4% | **MATCH** |
| **EXP-06** | Sub-Protocol 6A Replays | 100/100 (100.0%) | 100/100 (100.0%) | 100/100 (100.0%) | **MATCH** |
| **EXP-06** | Sub-Protocol 6B Checkpoints | 100/100 (100.0%) | 100/100 (100.0%) | 100/100 (100.0%) | **MATCH** |
| **EXP-06** | Reproduction Success Rate | 100.0% (200/200) | 100.0% (200/200) | 100.0% (200/200) | **MATCH** |

---

## 3. Claim Hierarchy Audit

| Claim in Manuscript v1.0 | P1-D2 Allowed Category | Actual Framing in Manuscript | Audit Status |
| :--- | :--- | :--- | :---: |
| Observation interface leaks 0.0% private info | Tier 1 (Established) | Confirmed via bitwise inspection of $\Omega_p(S)$ | **VALIDATED** |
| Latent states produce divergent trajectories | Tier 1 (Established) | Confirmed: 84.63% divergence, $p < 10^{-15}$ | **VALIDATED** |
| Simulator achieves bitwise deterministic reproducibility | Tier 1 (Established) | Confirmed: 200/200 exact SHA-256 matches | **VALIDATED** |
| Rule-based heuristics dominate random agents in asymmetric play | Tier 1 (Established) | Confirmed: 65.4% in 4P, 86.3% in 2P | **VALIDATED** |
| Symmetric 4P heuristic self-play stalls in defensive loops | Tier 1 (Established) | Documented honestly as 43.6% truncation | **VALIDATED** |
| Scaling dynamics undergo a marked shift at $\rho_0 > 1.0$ | Tier 2 (Qualified) | Framed empirically as a gameplay regime shift | **VALIDATED** |
| Multi-card penalty stacking is invariant against random play | Tier 2 (Qualified) | Explicitly qualified as opponent-policy dependent | **VALIDATED** |
| WHOT-ML is a laboratory for future RL research | Tier 2 (Qualified) | Formatted as benchmark foundation | **VALIDATED** |
| Sample complexity or RL convergence bounds | Tier 3 (Prohibited) | Completely absent; reserved for Paper 2 | **VALIDATED** |
| Optimal policy characterization | Tier 3 (Prohibited) | Completely absent; no optimal oracle assumed | **VALIDATED** |
| Human parity or human comparison | Tier 3 (Prohibited) | Completely absent; no human trials claimed | **VALIDATED** |

---

## 4. Audit of Prohibited Claims (12 Explicit Invariants)

| Prohibited Claim ID | Specific Prohibited Concept | Checked in Manuscript v1.0 | Finding |
| :---: | :--- | :--- | :--- |
| **1** | Claiming optimal actions differ in EXP-02 | Searched for "optimal action", "optimal policy" | **ABSENT** (framed as trajectory divergence) |
| **2** | Claiming "WHOT is solved" | Searched for "solved", "solves WHOT" | **ABSENT** |
| **3** | Claiming deep RL or CFR convergence | Searched for RL convergence proofs | **ABSENT** (RL reserved for Paper 2) |
| **4** | Claiming mathematical complexity class bounds | Searched for "NP-hard", "PSPACE", "EXPTIME" | **ABSENT** (combinatorial uncertainty used) |
| **5** | Claiming penalty stacking is useless | Searched for "stacking is useless/irrelevant" | **ABSENT** (qualified as opponent-dependent) |
| **6** | Claiming RuleBased is optimal or near-optimal | Searched for "RuleBased is optimal" | **ABSENT** (framed as behavioral floor) |
| **7** | Claiming RuleBased exhibits "intelligence" | Searched for "heuristic intelligence" | **ABSENT** (framed as deterministic heuristic) |
| **8** | Claiming formal thermodynamic phase transition | Searched for "phase transition" | **ABSENT** (framed as empirical regime shift) |
| **9** | Claiming partial observability is proven beyond observation equivalence | Searched for overclaimed POMDP proofs | **ABSENT** (framed strictly through rollout divergence) |
| **10** | Comparing performance against human players | Searched for "human-level", "human parity" | **ABSENT** |
| **11** | Reporting training sample efficiency or learning curves | Searched for training curves, sample efficiency | **ABSENT** |
| **12** | Blaming the 43.6% self-play truncation on a bug | Searched for "software bug", "engine error" | **ABSENT** (analyzed as emergent defensive stall) |

---

## 5. Stale Pilot Content Audit

A full-text automated search was executed across `WHOT-ML Paper 1 — Manuscript v1.0.md` for historical pilot artifacts:
- **Search `82.02%` (pilot EXP-02 divergence):** **0 occurrences** (superseded by 84.63%).
- **Search `100.0%` for BR_2P (pilot 2-player win rate):** **0 occurrences** (superseded by 86.3%).
- **Search `62.5%` (pilot BRRR win rate):** **0 occurrences** (superseded by 65.4%).
- **Search `72.5%` (drafting slip typo):** **0 occurrences** (completely purged).
- **Search `40/40` (pilot determinism count):** **0 occurrences** (superseded by 200/200).
- **Search `470` (pilot total run count):** **0 occurrences** (superseded by 12,350).

Zero stale pilot values were detected in any table, figure caption, abstract, or prose section.

---

## 6. Citation & Literature Integrity Audit

All 16 citations included in Section 18 of the manuscript were verified against standard academic databases:
1. `Bard et al. (2020)` — Artificial Intelligence: The Hanabi Challenge. (Authentic)
2. `Bellemare et al. (2013)` — JAIR: Arcade Learning Environment. (Authentic)
3. `Bowling et al. (2015)` — Science: Heads-up limit hold'em poker is solved. (Authentic)
4. `Brockman et al. (2016)` — arXiv: OpenAI Gym. (Authentic)
5. `Brown & Sandholm (2018)` — Science: Libratus. (Authentic)
6. `Brown & Sandholm (2019)` — Science: Pluribus multiplayer poker. (Authentic)
7. `Cliff (1993)` — Psychological Bulletin: Dominance statistics & Cliff's delta. (Authentic)
8. `Kaelbling et al. (1998)` — Artificial Intelligence: Planning & acting in POMDPs. (Authentic)
9. `Lanctot et al. (2019)` — arXiv: OpenSpiel. (Authentic)
10. `Littman (1994)` — ICML: Markov games framework. (Authentic)
11. `Moravčík et al. (2017)` — Science: DeepStack. (Authentic)
12. `Silver et al. (2018)` — Science: AlphaZero. (Authentic)
13. `Sutton & Barto (2018)` — MIT Press: Reinforcement Learning. (Authentic)
14. `Terry et al. (2021)` — NeurIPS: PettingZoo. (Authentic)
15. `Wilson (1927)` — JASA: Wilson score interval. (Authentic)
16. `Zha et al. (2019)` — arXiv / IJCAI: DouZero. (Authentic)

Zero hallucinated or unverified citations exist in the manuscript.

---

## 7. Simulator & Production Data Integrity

- **Git Commit Check:** `git rev-parse HEAD` returns `7c1a2dc23a277fdfb5e9052d4d90e3798fb24ea4`.
- **Core Engine Check:** `git diff 7c1a2dc -- whot_ml/` is strictly empty.
- **Production Archive Check:** `experiments/paper1/runs/kaggle_production_20261005_verified/whot_ml_production_artifacts.tar.gz` verified with SHA-256 `8a82d9f7529610b1beb408395f1bc6b9edd9c8d784dee9887c38e02599d4a13a`.
- **Local Test Suite:** 109 passing tests confirmed.

---

---

## 8. Technical Corrections, Polish & Encoding Verification

### 8.1 Technical Corrections against Frozen Simulator
The manuscript was factually aligned with the frozen simulator implementation in `whot_ml/`:

| Section | Item Corrected | Previous Draft Wording | Corrected Manuscript Text | Simulator Reference | Audit Verdict |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **3.4** | Action space discrete index mapping | 0–53 (54 physical cards), 54–73 (WHOT plays, 5×4=20) | **0–48:** 49 ordinary physical cards; **49–73:** WHOT plays (5 cards $\times$ 5 shapes = 25 actions); **74:** DRAW; **75:** DECLARE_LAST | `whot_ml/action.py:3-10` (`NUM_ORDINARY_CARDS=49`, $5\times 5=25$, `DRAW=74`, `DECLARE_LAST=75`) | **VERIFIED MATCH** |
| **3.6** | WHOT card naming | `Crown / WHOT (Card 20)` | `WHOT (Card 20)` | `whot_ml/card.py:16` (`Shape`, `CardType.WHOT`) | **VERIFIED MATCH** |
| **3.8** | Truncation game resolution | Penalty point summation determines winner by lowest hand score | Truncated games terminate without a winner (`winner = None`); reported separately from victories | `whot_ml/effect_resolver.py:373-376`, `whot_ml/environment.py:153-162` | **VERIFIED MATCH** |

### 8.2 Final Polish Items
1. **National Card Game Characterization:** Softened from "national card game of Nigeria" to "widely played card game in Nigeria" across Abstract, Introduction (Section 1), and Conclusion (Section 16).
2. **Reverse Direction Card Effect:** Removed "reverse direction" from the Introduction list of special card effects, aligning directly with implemented effects (Hold On, Suspension, General Market, Pick Two, Pick Three, WHOT).
3. **Markov Games Citation:** Added formal in-text citation to Littman (1994) in Section 2.1 (*Partially Observable Markov Decision Processes*).
4. **Pick Three Rule Clarification:** Clarified that Pick Three (Card 5) is enabled by default in `WHOT-NG-v1.0` (`whot_ml/ruleset.py:78`).

### 8.3 Encoding & String Rendering Verification
The manuscript was re-exported as clean UTF-8 without Byte Order Mark (BOM). All special typography, diacritics, mathematical operators, and Greek symbols were verified:

| Target String | Unicode Codepoints | Context in Manuscript | Audit Verification |
| :--- | :--- | :--- | :---: |
| **Moravčík** | U+004D, U+006F, U+0072, U+0061, U+0076, U+010D, U+00ED, U+006B | Sections 2.2, 7.3, 18 | **RENDERED & VERIFIED** |
| **Pérolat** | U+0050, U+00E9, U+0072, U+006F, U+006C, U+0061, U+0074 | Section 18 (OpenSpiel) | **RENDERED & VERIFIED** |
| **Lisý** | U+004C, U+0069, U+0073, U+00FD | Section 18 (DeepStack) | **RENDERED & VERIFIED** |
| **±** | U+00B1 | Abstract, Sections 6.1, 7.2 | **RENDERED & VERIFIED** |
| **δ** | U+03B4 | Section 10.2 (Cliff's $\delta$) | **RENDERED & VERIFIED** |
| **ρ₀** | U+03C1, U+2080 | Table 4 header, Section 9.2 | **RENDERED & VERIFIED** |
| **Ω** | U+03A9 | Sections 3.5, 7.1 | **RENDERED & VERIFIED** |
| **≥** | U+2265 | Sections 3.3, 9.2, 9.3, 15 | **RENDERED & VERIFIED** |
| **—** | U+2014 (Em-dash) | Across manuscript titles & prose | **RENDERED & VERIFIED** |
| **–** | U+2013 (En-dash) | Page intervals, numerical ranges | **RENDERED & VERIFIED** |
| **hold'em** | U+0068, U+006F, U+006C, U+0064, U+0027, U+0065, U+006D | Sections 2.2, 18 | **RENDERED & VERIFIED** |

### 8.4 Invariant Checks
1. **Numerical Round-Trip Audit:** Re-running the statistical verification across the raw production telemetry confirmed 58 / 58 metrics remain strictly identical with zero rounding or parsing shifts.
2. **Empirical Claims Preserved:** No claims, confidence intervals, or conclusions were altered.
3. **Core Simulator Frozen:** `git diff 7c1a2dc -- whot_ml/` is strictly empty.
4. **Test Suite:** 109 / 109 tests passing.
5. **Data Freeze Maintained:** Production dataset SHA-256 remains `8a82d9f7529610b1beb408395f1bc6b9edd9c8d784dee9887c38e02599d4a13a`.

---

## 9. Final Recommendation

`WHOT-ML Paper 1 — Manuscript v1.0.md` represents a complete, mathematically rigorous, clean UTF-8 encoded, and evidence-grounded research manuscript. With all technical corrections, polish items, and encoding verifications complete, it provides a publication-grade foundation.

```
================================================================================
FINAL AUDIT STATUS:
MANUSCRIPT READY FOR HUMAN REVIEW
================================================================================
```


