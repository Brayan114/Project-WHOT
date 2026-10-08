# Table 1: WHOT-NG-v1 Baseline Environment Characterization [FULL]

| Metric | RandomLegal Cohort | RuleBased Cohort | Environment Space |
| :--- | :--- | :--- | :--- |
| Physical Cards ($N_{deck}$) | 54 | 54 | 54 (Canonical Deck) |
| Action Space Size ($|A|$) | 76 | 76 | 76 Discrete Slots |
| Legal Actions (Mean $\pm$ SD) | 2.42 $\pm$ 2.40 | 7.63 $\pm$ 7.11 | - |
| Legal Actions (Median [IQR]) | 1.0 [1.0, 3.0] | 5.0 [2.0, 11.0] | - |
| Game Duration (Mean Turns) | 368.3 | 506.4 | - |
| Game Duration (Median [IQR]) | 270.5 [125.8, 546.2] | 248.0 [75.8, 1000.0] | - |
| Mean Draws per Game | 245.3 | 457.7 | - |
| Market Reshuffles per Game | 8.19 | 270.36 | - |
| Declaration Violations | 1079 | 0 | 0 (Heuristic Invariant) |
| Truncation Rate (95% CI) | 7.6% [6.1%, 9.4%] | 43.6% [40.6%, 46.7%] | Max 1000 Turns |
