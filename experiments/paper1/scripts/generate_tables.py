"""Publication table generation for Paper 1 (Stage 3B).

Generates LaTeX (.tex) and Markdown (.md) tables directly from processed summary metrics.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.paper1.scripts.common import ExperimentPaths


def generate_table1_characterization(pilot: bool = True, suffix: Optional[str] = None) -> Tuple[Path, Path]:
    """Table 1: Environment Characterization Summary."""
    if suffix is None:
        suffix = "pilot" if pilot else "full"
    with open(ExperimentPaths.PROCESSED / f"exp01_{suffix}_summary.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    cohorts = data["cohorts"]
    status_str = suffix.upper()

    # Markdown
    md_lines = [
        f"# Table 1: WHOT-NG-v1 Baseline Environment Characterization [{status_str}]\n",
        "| Metric | RandomLegal Cohort | RuleBased Cohort | Environment Space |",
        "| :--- | :--- | :--- | :--- |",
        f"| Physical Cards ($N_{{deck}}$) | 54 | 54 | 54 (Canonical Deck) |",
        f"| Action Space Size ($|A|$) | 76 | 76 | 76 Discrete Slots |",
        f"| Legal Actions (Mean $\\pm$ SD) | {cohorts['random_cohort']['legal_action_count']['mean']:.2f} $\\pm$ {cohorts['random_cohort']['legal_action_count']['std']:.2f} | {cohorts['rule_based_cohort']['legal_action_count']['mean']:.2f} $\\pm$ {cohorts['rule_based_cohort']['legal_action_count']['std']:.2f} | - |",
        f"| Legal Actions (Median [IQR]) | {cohorts['random_cohort']['legal_action_count']['median']:.1f} [{cohorts['random_cohort']['legal_action_count']['q25']:.1f}, {cohorts['random_cohort']['legal_action_count']['q75']:.1f}] | {cohorts['rule_based_cohort']['legal_action_count']['median']:.1f} [{cohorts['rule_based_cohort']['legal_action_count']['q25']:.1f}, {cohorts['rule_based_cohort']['legal_action_count']['q75']:.1f}] | - |",
        f"| Game Duration (Mean Turns) | {cohorts['random_cohort']['turn_count']['mean']:.1f} | {cohorts['rule_based_cohort']['turn_count']['mean']:.1f} | - |",
        f"| Game Duration (Median [IQR]) | {cohorts['random_cohort']['turn_count']['median']:.1f} [{cohorts['random_cohort']['turn_count']['q25']:.1f}, {cohorts['random_cohort']['turn_count']['q75']:.1f}] | {cohorts['rule_based_cohort']['turn_count']['median']:.1f} [{cohorts['rule_based_cohort']['turn_count']['q25']:.1f}, {cohorts['rule_based_cohort']['turn_count']['q75']:.1f}] | - |",
        f"| Mean Draws per Game | {cohorts['random_cohort']['draw_count']['mean']:.1f} | {cohorts['rule_based_cohort']['draw_count']['mean']:.1f} | - |",
        f"| Market Reshuffles per Game | {cohorts['random_cohort']['market_reshuffles'] / cohorts['random_cohort']['games_played']:.2f} | {cohorts['rule_based_cohort']['market_reshuffles'] / cohorts['rule_based_cohort']['games_played']:.2f} | - |",
        f"| Declaration Violations | {cohorts['random_cohort']['declaration_violations']} | {cohorts['rule_based_cohort']['declaration_violations']} | 0 (Heuristic Invariant) |",
        f"| Truncation Rate (95% CI) | {cohorts['random_cohort']['truncation']['point']:.1%} [{cohorts['random_cohort']['truncation']['ci_lower']:.1%}, {cohorts['random_cohort']['truncation']['ci_upper']:.1%}] | {cohorts['rule_based_cohort']['truncation']['point']:.1%} [{cohorts['rule_based_cohort']['truncation']['ci_lower']:.1%}, {cohorts['rule_based_cohort']['truncation']['ci_upper']:.1%}] | Max 1000 Turns |",
    ]
    md_path = ExperimentPaths.TABLES / f"table1_characterization_{suffix}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    # LaTeX
    tex_lines = [
        "\\begin{table}[ht]",
        "\\centering",
        f"\\caption{{WHOT-NG-v1 Baseline Environment Characterization [{status_str}]}}",
        "\\begin{tabular}{lccc}",
        "\\hline",
        "Metric & RandomLegal & RuleBased & Environment Space \\\\",
        "\\hline",
        f"Physical Cards ($N_{{deck}}$) & 54 & 54 & 54 \\\\",
        f"Action Space Size ($|A|$) & 76 & 76 & 76 \\\\",
        f"Legal Actions (Mean $\\pm$ SD) & {cohorts['random_cohort']['legal_action_count']['mean']:.2f} $\\pm$ {cohorts['random_cohort']['legal_action_count']['std']:.2f} & {cohorts['rule_based_cohort']['legal_action_count']['mean']:.2f} $\\pm$ {cohorts['rule_based_cohort']['legal_action_count']['std']:.2f} & - \\\\",
        f"Mean Game Duration (Turns) & {cohorts['random_cohort']['turn_count']['mean']:.1f} & {cohorts['rule_based_cohort']['turn_count']['mean']:.1f} & - \\\\",
        f"Mean Draws / Game & {cohorts['random_cohort']['draw_count']['mean']:.1f} & {cohorts['rule_based_cohort']['draw_count']['mean']:.1f} & - \\\\",
        f"Truncation Rate & {cohorts['random_cohort']['truncation']['point'] * 100:.1f}\\% & {cohorts['rule_based_cohort']['truncation']['point'] * 100:.1f}\\% & - \\\\",
        "\\hline",
        "\\end{tabular}",
        "\\end{table}",
    ]
    tex_path = ExperimentPaths.TABLES / f"table1_characterization_{suffix}.tex"
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write("\n".join(tex_lines) + "\n")

    return md_path, tex_path


def generate_table2_partial_observability(pilot: bool = True, suffix: Optional[str] = None) -> Tuple[Path, Path]:
    """Table 2: Partial Observability Summary."""
    if suffix is None:
        suffix = "pilot" if pilot else "full"
    with open(ExperimentPaths.PROCESSED / f"exp02_{suffix}_summary.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    status_str = suffix.upper()
    md_lines = [
        f"# Table 2: Partial Observability Equivalence and Divergence [{status_str}]\n",
        "| Metric | Empirical Value | Formal Requirement |",
        "| :--- | :--- | :--- |",
        f"| State Pairs Evaluated | {data['total_pairs_tested']} | $\\ge 30$ |",
        f"| Observation Equivalence Rate | {data['equivalence_verification_rate']:.1%} | 100.0% ($S_a \\neq S_b \\implies \\Omega_p(S_a) = \\Omega_p(S_b)$) |",
        f"| Information Leakage Rate | {data['information_leak_rate']:.1%} | 0.0% (Zero hidden cards in observation) |",
        f"| Overall Trajectory Divergence Rate | {data['overall_divergence_rate']:.1%} | Recorded (non-divergence is not failure) |",
        f"| Opponent-Swap Divergence Rate | {data['mode_divergence_rates'].get('OPPONENT_SWAP', 0.0):.1%} | - |",
        f"| Market-Reversal Divergence Rate | {data['mode_divergence_rates'].get('MARKET_REVERSAL', 0.0):.1%} | - |",
        f"| Opponent-Market Divergence Rate | {data['mode_divergence_rates'].get('OPPONENT_MARKET_SWAP', 0.0):.1%} | - |",
        f"| Mean Log Hidden Uncertainty $\\log_{{10}}|\\mathcal{{S}}(\\Omega)|$ | {data['log_uncertainty_stats']['mean']:.2f} | $\\ge 10^{{15}}$ Combinations |",
    ]
    md_path = ExperimentPaths.TABLES / f"table2_partial_observability_{suffix}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    tex_path = ExperimentPaths.TABLES / f"table2_partial_observability_{suffix}.tex"
    tex_lines = [
        "\\begin{table}[ht]",
        "\\centering",
        f"\\caption{{Partial Observability Equivalence and Divergence Verification [{status_str}]}}",
        "\\begin{tabular}{lcc}",
        "\\hline",
        "Metric & Empirical Value & Invariant Target \\\\",
        "\\hline",
        f"Equivalence Rate & {data['equivalence_verification_rate'] * 100:.1f}\\% & 100.0\\% \\\\",
        f"Information Leakage Rate & {data['information_leak_rate'] * 100:.1f}\\% & 0.0\\% \\\\",
        f"Trajectory Divergence Rate & {data['overall_divergence_rate'] * 100:.1f}\\% & Observable Divergence \\\\",
        f"Mean $\\log_{{10}}|\\mathcal{{S}}(\\Omega)|$ & {data['log_uncertainty_stats']['mean']:.2f} & - \\\\",
        "\\hline",
        "\\end{tabular}",
        "\\end{table}",
    ]
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write("\n".join(tex_lines) + "\n")

    return md_path, tex_path


def generate_table3_baselines(pilot: bool = True, suffix: Optional[str] = None) -> Tuple[Path, Path]:
    """Table 3: Baseline Agent Tournament Summary."""
    if suffix is None:
        suffix = "pilot" if pilot else "full"
    with open(ExperimentPaths.PROCESSED / f"exp03_{suffix}_summary.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    status_str = suffix.upper()
    md_lines = [
        f"# Table 3: Baseline Agent Matchup Characterization [{status_str}]\n",
        "| Matchup | Target Agent | Win Rate (95% CI) | Avg Finishing Rank | Mean Turns | Draws/Game | Truncation % |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for m_id, m_data in data["matchups"].items():
        wr_stats = m_data["win_rate_stats"]
        for atype, stat in wr_stats.items():
            rank_mean = m_data["rank_stats"].get(atype, {}).get("mean", 0.0)
            md_lines.append(
                f"| {m_id} | {atype} | {stat['point']:.1%} [{stat['ci_lower']:.1%}, {stat['ci_upper']:.1%}] | {rank_mean:.2f} | {m_data['turn_length']['mean']:.1f} | {m_data['draw_count']['mean']:.1f} | {m_data['truncation']['point']:.1%} |"
            )

    md_path = ExperimentPaths.TABLES / f"table3_baselines_{suffix}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    tex_path = ExperimentPaths.TABLES / f"table3_baselines_{suffix}.tex"
    tex_lines = [
        "\\begin{table}[ht]",
        "\\centering",
        f"\\caption{{Baseline Agent Tournament Summary [{status_str}]}}",
        "\\begin{tabular}{lcccccc}",
        "\\hline",
        "Matchup & Agent & Win Rate (95\\% CI) & Rank & Turns & Draws & Trunc \\\\",
        "\\hline",
    ]
    for m_id, m_data in data["matchups"].items():
        for atype, stat in m_data["win_rate_stats"].items():
            rank_mean = m_data["rank_stats"].get(atype, {}).get("mean", 0.0)
            tex_lines.append(
                f"{m_id} & {atype} & {stat['point'] * 100:.1f}\\% [{stat['ci_lower'] * 100:.1f}\\%, {stat['ci_upper'] * 100:.1f}\\%] & {rank_mean:.2f} & {m_data['turn_length']['mean']:.1f} & {m_data['draw_count']['mean']:.1f} & {m_data['truncation']['point'] * 100:.1f}\\% \\\\"
            )
    tex_lines.extend(["\\hline", "\\end{tabular}", "\\end{table}"])
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write("\n".join(tex_lines) + "\n")

    return md_path, tex_path


def generate_table4_scaling(pilot: bool = True, suffix: Optional[str] = None) -> Tuple[Path, Path]:
    """Table 4: Player Count Scaling Summary."""
    if suffix is None:
        suffix = "pilot" if pilot else "full"
    with open(ExperimentPaths.PROCESSED / f"exp04_{suffix}_summary.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    status_str = suffix.upper()
    md_lines = [
        f"# Table 4: Player Count Scaling Dynamics $N \\in \\{{2..6\\}}$ [{status_str}]\n",
        "| $N$ | Initial Market $|M_0|$ | Opponent Cards $|C_{opp}|$ | Opp/Market Ratio $\\rho_0$ | Mean Turns | Turns/Player | Draws/Game | Reshuffles |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for n_str, res in sorted(data["scaling_results"].items(), key=lambda x: int(x[0])):
        md_lines.append(
            f"| {res['player_count']} | {res['initial_market_size']} | {res['initial_opponent_cards']} | {res['initial_opp_to_market_ratio']:.3f} | {res['turn_count']['mean']:.1f} | {res['turns_per_player']['mean']:.1f} | {res['draw_count']['mean']:.1f} | {res['market_reshuffles']['mean']:.2f} |"
        )

    md_path = ExperimentPaths.TABLES / f"table4_scaling_{suffix}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    tex_path = ExperimentPaths.TABLES / f"table4_scaling_{suffix}.tex"
    tex_lines = [
        "\\begin{table}[ht]",
        "\\centering",
        f"\\caption{{Player Count Scaling Summary $N \\in \\{{2..6\\}}$ [{status_str}]}}",
        "\\begin{tabular}{cccccccc}",
        "\\hline",
        "$N$ & $|M_0|$ & $|C_{opp}|$ & $\\rho_0$ & Turns & Turns/Player & Draws & Reshuffles \\\\",
        "\\hline",
    ]
    for n_str, res in sorted(data["scaling_results"].items(), key=lambda x: int(x[0])):
        tex_lines.append(
            f"{res['player_count']} & {res['initial_market_size']} & {res['initial_opponent_cards']} & {res['initial_opp_to_market_ratio']:.3f} & {res['turn_count']['mean']:.1f} & {res['turns_per_player']['mean']:.1f} & {res['draw_count']['mean']:.1f} & {res['market_reshuffles']['mean']:.2f} \\\\"
        )
    tex_lines.extend(["\\hline", "\\end{tabular}", "\\end{table}"])
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write("\n".join(tex_lines) + "\n")

    return md_path, tex_path


def generate_table5_rule_variants(pilot: bool = True, suffix: Optional[str] = None) -> Tuple[Path, Path]:
    """Table 5: Controlled Rule Variants Summary."""
    if suffix is None:
        suffix = "pilot" if pilot else "full"
    with open(ExperimentPaths.PROCESSED / f"exp05_{suffix}_summary.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    status_str = suffix.upper()
    md_lines = [
        f"# Table 5: Controlled Rule Variant Ablations [{status_str}]\n",
        "| Variant ID | Description | Mean Turns | $\\Delta$ Turns vs Base | Cliff's $\\delta$ | Mean Draws | RuleBased Win % |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    base_turns = data["variants"]["VAR-BASE"]["turn_count"]["mean"]
    for v_id, v_data in data["variants"].items():
        delta_str = "-"
        cliff_str = "-"
        if v_id != "VAR-BASE" and v_id in data["paired_comparisons_vs_base"]:
            comp = data["paired_comparisons_vs_base"][v_id]
            delta_val = comp["turn_diff_stats"]["mean"]
            delta_str = f"{delta_val:+.1f}"
            cliff_str = f"{comp['turn_cliffs_delta']:.2f}"

        md_lines.append(
            f"| {v_id} | {v_data['description']} | {v_data['turn_count']['mean']:.1f} | {delta_str} | {cliff_str} | {v_data['draw_count']['mean']:.1f} | {v_data['rule_based_win_rate']['point']:.1%} |"
        )

    md_path = ExperimentPaths.TABLES / f"table5_rule_variants_{suffix}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    tex_path = ExperimentPaths.TABLES / f"table5_rule_variants_{suffix}.tex"
    tex_lines = [
        "\\begin{table}[ht]",
        "\\centering",
        f"\\caption{{Controlled Rule Variant Ablations [{status_str}]}}",
        "\\begin{tabular}{lccccc}",
        "\\hline",
        "Variant ID & Description & Turns & $\\Delta$ Turns & Cliff's $\\delta$ & RuleBased Win \\\\",
        "\\hline",
    ]
    for v_id, v_data in data["variants"].items():
        delta_str = "-"
        cliff_str = "-"
        if v_id != "VAR-BASE" and v_id in data["paired_comparisons_vs_base"]:
            comp = data["paired_comparisons_vs_base"][v_id]
            delta_str = f"{comp['turn_diff_stats']['mean']:+.1f}"
            cliff_str = f"{comp['turn_cliffs_delta']:.2f}"
        tex_lines.append(
            f"{v_id} & {v_data['description']} & {v_data['turn_count']['mean']:.1f} & {delta_str} & {cliff_str} & {v_data['rule_based_win_rate']['point'] * 100:.1f}\\% \\\\"
        )
    tex_lines.extend(["\\hline", "\\end{tabular}", "\\end{table}"])
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write("\n".join(tex_lines) + "\n")

    return md_path, tex_path


def generate_table6_determinism(pilot: bool = True, suffix: Optional[str] = None) -> Tuple[Path, Path]:
    """Table 6: Determinism & Checkpoint Restoration Audit."""
    if suffix is None:
        suffix = "pilot" if pilot else "full"
    with open(ExperimentPaths.PROCESSED / f"exp06_{suffix}_summary.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    status_str = suffix.upper()
    md_lines = [
        f"# Table 6: Determinism and State Checkpoint Restoration Audit [{status_str}]\n",
        "| Sub-Protocol | Test Target | Tests Executed | Exact Matches | Success Rate | Invariant Target |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
        f"| Sub-Protocol 6A | Independent Deterministic Replay | {data['replays_tested']} | {data['replays_matched']} | {data['replay_success_rate']:.1%} | 100.0% Exact Hash Match |",
        f"| Sub-Protocol 6B | Mid-Game Checkpoint Restoration | {data['checkpoints_tested']} | {data['checkpoints_matched']} | {data['checkpoint_success_rate']:.1%} | 100.0% Continuation Parity |",
        f"| **Overall** | **Reproduction Success Rate (RSR)** | **{data['total_tests']}** | **{data['total_passed']}** | **{data['reproduction_success_rate_percent']:.1f}%** | **100.0% Zero Tolerance** |",
    ]
    md_path = ExperimentPaths.TABLES / f"table6_determinism_{suffix}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    tex_path = ExperimentPaths.TABLES / f"table6_determinism_{suffix}.tex"
    tex_lines = [
        "\\begin{table}[ht]",
        "\\centering",
        f"\\caption{{Determinism and State Checkpoint Restoration Audit [{status_str}]}}",
        "\\begin{tabular}{lcccc}",
        "\\hline",
        "Sub-Protocol & Tests & Matches & Success Rate & Target \\\\",
        "\\hline",
        f"Independent Replay & {data['replays_tested']} & {data['replays_matched']} & {data['replay_success_rate'] * 100:.1f}\\% & 100.0\\% \\\\",
        f"Checkpoint Restoration & {data['checkpoints_tested']} & {data['checkpoints_matched']} & {data['checkpoint_success_rate'] * 100:.1f}\\% & 100.0\\% \\\\",
        f"\\textbf{{Overall RSR}} & \\textbf{{{data['total_tests']}}} & \\textbf{{{data['total_passed']}}} & \\textbf{{{data['reproduction_success_rate_percent']:.1f}\\%}} & \\textbf{{100.0\\%}} \\\\",
        "\\hline",
        "\\end{tabular}",
        "\\end{table}",
    ]
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write("\n".join(tex_lines) + "\n")

    return md_path, tex_path


def generate_all_tables(pilot: bool = True, suffix: Optional[str] = None) -> None:
    """Generate all markdown and LaTeX tables for Paper 1."""
    ExperimentPaths.ensure_directories()
    mode_str = suffix.upper() if suffix else ("PILOT" if pilot else "FULL")
    print(f"\n[TABLES] Generating publication tables ({mode_str})...")

    t1_md, t1_tex = generate_table1_characterization(pilot=pilot, suffix=suffix)
    print(f"  Table 1: {t1_md} and {t1_tex}")

    t2_md, t2_tex = generate_table2_partial_observability(pilot=pilot, suffix=suffix)
    print(f"  Table 2: {t2_md} and {t2_tex}")

    t3_md, t3_tex = generate_table3_baselines(pilot=pilot, suffix=suffix)
    print(f"  Table 3: {t3_md} and {t3_tex}")

    t4_md, t4_tex = generate_table4_scaling(pilot=pilot, suffix=suffix)
    print(f"  Table 4: {t4_md} and {t4_tex}")

    t5_md, t5_tex = generate_table5_rule_variants(pilot=pilot, suffix=suffix)
    print(f"  Table 5: {t5_md} and {t5_tex}")

    t6_md, t6_tex = generate_table6_determinism(pilot=pilot, suffix=suffix)
    print(f"  Table 6: {t6_md} and {t6_tex}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Paper 1 Tables")
    parser.add_argument("--full", action="store_true", help="Generate from full data instead of pilot")
    parser.add_argument("--dry-run", action="store_true", help="Generate from dry-run data")
    args = parser.parse_args()
    suffix_arg = "dry_run" if args.dry_run else ("full" if args.full else "pilot")
    generate_all_tables(pilot=not args.full, suffix=suffix_arg)
