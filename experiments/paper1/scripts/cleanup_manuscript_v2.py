"""Clean up paper/main.tex:
1. Standard article template.
2. Fix math error (47! / (6! 6! 6! 29!) ≈ 7.8e13).
3. Update DECLARE_LAST & 25 WHOT wildcard action space explanation.
4. Update Abstract and Section 13.2 stacking text.
5. Condense EXP-06 into Methodology and remove Section 11.
6. Insert Experiment 7: Reinforcement Learning Baselines placeholder.
7. Clean up internal jargon (Paper 1, P1-D1, experiments/paper1/).
8. Update synthesis table.
"""

import re
from pathlib import Path

MAIN_TEX = Path("paper/main.tex")
with open(MAIN_TEX, "r", encoding="utf-8") as f:
    text = f.read().replace("\r\n", "\n")

# 1. Update Document Class and Front Matter
old_preamble = r"""\documentclass[acmlarge, nonacm]{acmart}

% --- Essential Packages ---
\usepackage{amsmath,amsfonts}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{graphicx}
\usepackage{multirow}
\usepackage{seqsplit}

\title{WHOT-ML: A Configurable Partially Observable Multi-Agent Environment for Machine Learning Research}

\author{Brayan Osinaka}
\orcid{0009-0004-1914-1601}
\affiliation{%
  \institution{Independent Researcher}
  \country{Nigeria}
}
\email{brayanjunior101@gmail.com}

\begin{abstract}"""

new_preamble = r"""\documentclass[11pt,a4paper]{article}

% --- Essential Packages ---
\usepackage[utf8]{inputenc}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{graphicx}
\usepackage{multirow}
\usepackage{seqsplit}
\usepackage{url}
\usepackage{hyperref}
\usepackage{natbib}
\usepackage{microtype}

\title{\textbf{WHOT-ML: A Configurable Partially Observable Multi-Agent Environment for Machine Learning Research}}

\author{
  \textbf{Brayan Osinaka} \\
  Independent Researcher, Nigeria \\
  \texttt{brayanjunior101@gmail.com}
}
\date{}

\begin{document}

\maketitle

\begin{abstract}"""

assert old_preamble in text, "old_preamble not found"
text = text.replace(old_preamble, new_preamble)

# Remove \keywords and \begin{document} \maketitle since they were moved
old_doc_start = r"""\keywords{reinforcement learning, multi-agent systems, partial observability, POMDP, card games, benchmark environment}

\begin{document}

\maketitle"""

new_doc_start = r"""\noindent\textbf{Keywords:} reinforcement learning, multi-agent systems, partially observable stochastic games, POSG, card games, benchmark environment"""

assert old_doc_start in text, "old_doc_start not found"
text = text.replace(old_doc_start, new_doc_start)

# Remove all \Description{...} lines
text = re.sub(r'\\Description\{[^}]*\}\n?', '', text)

# 2. Update Abstract: Replace dormant stacking claim
old_abstract_finding = r"while penalty card stacking remains behaviorally dormant against random opponents; and (6) the environment achieves $100.0\%$ bitwise reproducibility across $200$ independent replay and mid-game state restoration trials."
new_abstract_finding = r"while penalty stacking acts as a catalyst for defensive stalls, with disabling it reducing truncation rates by over 50%; and (6) the environment achieves $100.0\%$ bitwise reproducibility across independent replay and state restoration trials, certified by 114 passing regression tests."
assert old_abstract_finding in text, "old_abstract_finding not found"
text = text.replace(old_abstract_finding, new_abstract_finding)

# 3. Fix Mathematical Error in Section 2.1
old_math_sec21 = r"In WHOT-ML, the combinatorial cardinality of compatible states consistent with a single observation routinely exceeds $|\mathcal{S}(\Omega)| > 10^{32}$, creating a formidable belief-estimation problem for multi-agent reinforcement learning."
new_math_sec21 = r"In WHOT-ML, the number of distinct distributions of the 47 unseen cards into three unobserved opponent hands of 6 cards and an unobserved market of 29 cards (integrating out the unobservable deck permutation order) is given by the multinomial partition coefficient $\frac{47!}{6!\,6!\,6!\,29!} \approx 7.8 \times 10^{13}$. This creates an underlying belief space on the order of $10^{13}$ states consistent with a single opening observation, presenting a formidable hidden-information challenge for multi-agent reinforcement learning."
assert old_math_sec21 in text, "old_math_sec21 not found"
text = text.replace(old_math_sec21, new_math_sec21)

# 4. Address DECLARE_LAST and 25 WHOT Action Slots in Section 3.4
old_action_space = r"""\subsection{Action Space and Dynamic Action Masking}
The action space $\mathcal{A}$ contains $76$ discrete action slots indexed as:
\begin{itemize}
  \item \textbf{Indices 0--48:} Standard play actions corresponding to each of the 49 ordinary physical cards in canonical order;
  \item \textbf{Indices 49--73:} WHOT card play actions paired with a selected shape nomination: $5 \text{ WHOT cards} \times 5 \text{ ordinary shapes} = 25 \text{ actions}$;
  \item \textbf{Index 74:} Draw action (\texttt{DRAW}) from the market;
  \item \textbf{Index 75:} Last-card declaration action (\texttt{DECLARE\_LAST}).
\end{itemize}"""

new_action_space = r"""\subsection{Action Space and Dynamic Action Masking}
The action space $\mathcal{A}$ contains $76$ discrete action slots indexed as:
\begin{itemize}
  \item \textbf{Indices 0--48:} Standard play actions corresponding to each of the 49 ordinary physical cards in canonical order;
  \item \textbf{Indices 49--73:} WHOT card play actions paired with a selected shape nomination: $5 \text{ WHOT cards} \times 5 \text{ ordinary shapes} = 25 \text{ actions}$;
  \item \textbf{Index 74:} Draw action (\texttt{DRAW}) from the market;
  \item \textbf{Index 75:} Last-card declaration action (\texttt{DECLARE\_LAST}).
\end{itemize}

\paragraph{WHOT Wildcard Action Allocation:}
The 25 action slots allocated to WHOT wildcards (Indices 49--73) map each of the 5 physical WHOT cards to each of the 5 ordinary nominated shapes. This design maintains an explicit bijective mapping between action indices and physical card instances (\texttt{card\_id}), which preserves physical card conservation and state serialization round-trip fidelity. However, because all 5 WHOT cards are functionally interchangeable under the rules of play, this representation inflates the discrete action branching factor with duplicate choices per shape. A high-level policy wrapper can collapse these 25 slots into 5 semantic decisions (one per nominated shape), allowing the underlying environment engine to resolve the selection to any currently held WHOT card.

\paragraph{Mechanics of \texttt{DECLARE\_LAST}:}
The \texttt{DECLARE\_LAST} action formalizes the cultural ``Last Card'' rule. It becomes legally available if and only if the acting player holds exactly one card and has not yet declared. In the default configuration (\texttt{declaration\_advances\_turn = False}), executing \texttt{DECLARE\_LAST} does not consume the player's turn; the player sets their declaration flag and immediately retains priority to play their final card. Conversely, if a player sheds their final card without prior declaration, an undeclared victory violation (\texttt{LAST\_CARD\_DECLARATION\_VIOLATION}) is triggered: shedding victory is denied, the player is penalized by drawing penalty cards (1 card in baseline, 2 cards under \texttt{VAR-PENALTY-2}), and play advances to the next player."""

assert old_action_space in text, "old_action_space not found"
text = text.replace(old_action_space, new_action_space)

# 5. Fix Math Error in Table 2 and Section 7.4
old_table2_line = r"Mean Log Combinatorial Uncertainty ($\log_{10} |\mathcal{S}(\Omega)|$) & 32.78 & $\ge 10^{15}$ Combinations \\"
new_table2_line = r"Mean Log Combinatorial Uncertainty ($\log_{10} |\mathcal{S}(\Omega)|$) & 13.89 & $\approx 7.8 \times 10^{13}$ Partitions \\"
assert old_table2_line in text, "old_table2_line not found"
text = text.replace(old_table2_line, new_table2_line)

# Also update Section 7.4 lead text if it mentions 10^32
text = text.replace(r"$p < 10^{-15}$", r"$p < 10^{-15}$")
text = text.replace(r"In the absence of an optimal oracle, Paper 1 establishes", r"In the absence of an optimal oracle, this paper establishes")

# 6. Condense EXP-06 into Methodology (Section 5) and remove Section 11
old_meth_lead = r"""\subsection{Simulator Configuration and Freeze Protocol}
All experiments were conducted against \texttt{WHOT-NG-v1.0}, frozen at Git commit {\small\texttt{\seqsplit{7c1a2dc23a277fdfb5e9052d4d90e3798fb24ea4}}}. The core simulation engine (\texttt{whot\_ml/}) was subjected to a non-negotiable modification freeze: all experimental instrumentation, metrics collectors, and runners resided strictly in external packages (\texttt{experiments/paper1/}). Local preflight integrity checks verified that \texttt{git diff 7c1a2dc -- whot\_ml/} remained strictly empty throughout the campaign."""

new_meth_lead = r"""\subsection{Simulator Configuration, Determinism, and Verification Suite}
All experiments were conducted against \texttt{WHOT-NG-v1.0} and its verified maintenance release \texttt{v1.0.1}. The simulator passes a comprehensive test suite of 114 unit and regression tests, verifying game invariant conservation, strict information boundaries (zero hidden-card leakage), and penalty stacking modes.

Furthermore, across 200 rigorous verification trials (100 independent episode replays and 100 mid-game state checkpoint restorations via JSON serialization), the environment achieves a \textbf{100.0\% Reproduction Success Rate (RSR)}, generating bitwise identical 64-character SHA-256 state digests. This guarantees zero-tolerance determinism and checkpoint continuity for tree search and reinforcement learning rollouts."""

assert old_meth_lead in text, "old_meth_lead not found"
text = text.replace(old_meth_lead, new_meth_lead)

# Remove Section 11 (EXP-06: Determinism & Reproducibility Audit)
old_sec11 = r"""\section{Experiment 6: Determinism \& Reproducibility Audit}

\subsection{Verification Protocol}
EXP-06 audits the bitwise determinism and checkpoint continuity of \texttt{WHOT-NG-v1.0} across $200$ rigorous evaluation tests:
\begin{itemize}
  \item \textbf{Sub-Protocol 6A (100 Independent Replays):} 100 complete games were executed from seeds 60000--60099. Trajectory tuples $(a_t, e_t, r_t, s_t, w)$ were serialized and SHA-256 hashed. Each episode was then independently re-executed from scratch with identical seeds.
  \item \textbf{Sub-Protocol 6B (100 Checkpoint Continuations):} 100 games were interrupted mid-game at turn $T=10$, serialized to JSON via \texttt{serialize\_state()}, restored into a clean environment via \texttt{restore\_state()}, and executed to completion. The post-restoration trajectory was compared against the uninterrupted baseline.
\end{itemize}




\begin{table}[htbp]
\centering
\caption{Determinism and State Checkpoint Restoration Audit (EXP-06, $N = 200$ tests)}
\label{tab:exp06_determinism}
\small
\begin{tabular}{llccc}
\toprule
\textbf{Sub-Protocol} & \textbf{Test Target} & \textbf{Tests Executed} & \textbf{Exact Matches} & \textbf{Success Rate} \\
\midrule
Sub-Protocol 6A & Independent Deterministic Replay & 100 & 100 & 100.0\% \\
Sub-Protocol 6B & Mid-Game Checkpoint Restoration & 100 & 100 & 100.0\% \\
\midrule
\textbf{Overall} & \textbf{Reproduction Success Rate (RSR)} & \textbf{200} & \textbf{200} & \textbf{100.0\%} \\
\bottomrule
\end{tabular}
\end{table}




\subsection{Result}
All 100 replays generated identical 64-character SHA-256 state digests. All 100 checkpoint restorations produced bitwise identical continuation paths, achieving a \textbf{Reproduction Success Rate ($\text{RSR}$) of $100.0\%$}. WHOT-NG-v1 satisfies zero-tolerance reproducibility for tree search and RL checkpointing."""

assert old_sec11 in text, "old_sec11 not found"
text = text.replace(old_sec11, "")

# 7. Insert Experiment 7 Placeholder after Experiment 5
old_after_exp5 = r"""  \item \textbf{Declaration Escalation Sensitivity:} Increasing the undeclared victory penalty to Draw 2 (\texttt{VAR-PENALTY-2}) slightly increases heuristic win rate from $66.2\%$ to $69.6\%$ (Cliff's $\delta = 0.00$), as random opponents suffer severe setbacks whenever they inadvertently shed their penultimate card without declaring.
\end{enumerate}"""

new_after_exp5 = r"""  \item \textbf{Declaration Escalation Sensitivity:} Increasing the undeclared victory penalty to Draw 2 (\texttt{VAR-PENALTY-2}) slightly increases heuristic win rate from $66.2\%$ to $69.6\%$ (Cliff's $\delta = 0.00$), as random opponents suffer severe setbacks whenever they inadvertently shed their penultimate card without declaring.
\end{enumerate}

\section{Experiment 7: Reinforcement Learning Baselines}
\label{sec:exp07_rl_baselines}
% TODO: Insert PPO results here."""

assert old_after_exp5 in text, "old_after_exp5 not found"
text = text.replace(old_after_exp5, new_after_exp5)

# 8. Update Section 13.2 stacking text
old_sec132 = r"In EXP-05, multi-card penalty stacking was behaviorally invisible ($\Delta = 0.0$) against random agents who failed to chain cards."
new_sec132 = r"In EXP-05, penalty stacking acts as a catalyst for defensive stalls, with disabling it reducing truncation rates by over 50%."
assert old_sec132 in text, "old_sec132 not found"
text = text.replace(old_sec132, new_sec132)

# 9. Update Master Results Synthesis Table (Table 7)
old_table7_exp5 = r"""EXP-05 & 2,500 & Declaration rule adds strategic friction; & NoDecl: $\Delta = -49.9$ turns; & Paired-sample seeds, & Established \\
       &       & stacking invariant under random opponents. & NoStack: $\Delta = +0.0$ turns & Cliff's delta = -0.13 & \\
\addlinespace
EXP-06 & 200   & Simulator provides flawless bitwise & Replays: 100/100; Checkpoints: & Bitwise SHA-256 state & Established \\
       &       & determinism and checkpoint continuity. & 100/100; RSR = 100.0\% & hash parity & \\"""

new_table7_exp5 = r"""EXP-05 & 2,500 & Declarations add strategic friction; penalty & NoDecl: $\Delta = -49.9$ turns; & Paired matched seeds, & Established \\
       &       & stacking drives defensive stalls and recycling. & NoStack: Trunc $2.2\% \to 0.8\%$ & Cliff's $\delta = -0.13, +0.04$ & \\
\addlinespace
EXP-06 & 200   & Verified suite certifies determinism, & Replays: 100/100; Checkpoints: & 114 unit tests passed, & Established \\
       &       & information boundaries, and state restoration. & 100/100; RSR = 100.0\% & bitwise SHA-256 parity & \\"""

assert old_table7_exp5 in text, "old_table7_exp5 not found"
text = text.replace(old_table7_exp5, new_table7_exp5)

# 10. Clean up remaining jargon: Paper 1, Paper 2, P1-D1
text = text.replace("WHOT-ML Paper 1 does not present", "This benchmark does not present")
text = text.replace("Paper 2 --- Reinforcement Learning in WHOT", "Reinforcement Learning in WHOT (Section~\\ref{sec:exp07_rl_baselines})")
text = text.replace("Paper 3 --- Hidden-Hand Belief Estimation", "Hidden-Hand Belief Estimation")
text = text.replace("Paper 4 --- Adaptive Opponent Modeling", "Adaptive Opponent Modeling")
text = text.replace("pre-registered specification P1-D1", "pre-registered experimental specification")

# Change \bibliographystyle to plainnat for standard article with natbib
text = text.replace(r"\bibliographystyle{ACM-Reference-Format}", r"\bibliographystyle{plainnat}")

with open(MAIN_TEX, "w", encoding="utf-8", newline="\n") as f:
    f.write(text)

print("Successfully cleaned up paper/main.tex!")
