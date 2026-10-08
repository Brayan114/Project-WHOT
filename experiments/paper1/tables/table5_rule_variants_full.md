# Table 5: Controlled Rule Variant Ablations [FULL]

| Variant ID | Description | Mean Turns | $\Delta$ Turns vs Base | Cliff's $\delta$ | Mean Draws | RuleBased Win % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| VAR-BASE | Baseline WHOT-NG-v1 default rules | 223.3 | - | - | 151.2 | 66.2% |
| VAR-NO-STACK-2 | Pick-2 penalty stacking disabled | 223.3 | +0.0 | 0.00 | 151.2 | 66.2% |
| VAR-NO-STACK-3 | Pick-3 penalty stacking disabled | 223.3 | +0.0 | 0.00 | 151.2 | 66.2% |
| VAR-NO-DECL | Last-card declaration rule disabled | 173.4 | -49.9 | -0.13 | 118.8 | 53.4% |
| VAR-PENALTY-2 | Last-card declaration violation penalty increased to DRAW_2 | 221.7 | -1.6 | 0.00 | 150.4 | 69.6% |
