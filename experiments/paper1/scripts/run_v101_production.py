"""Production runner for Paper 1 v1.0.1 verification: EXP-04a, EXP-04b, and EXP-05.

Executes:
1. EXP-04a: Player Count Scaling (RandomLegalAgent) across N in {2..6} (500 games each, seeds 40000..40499).
2. EXP-04b: Player Count Scaling (RuleBasedAgent) across N in {2..6} (500 games each, seeds 40000..40499).
3. EXP-05: Controlled Rule Variants on fixed v1.0.1 simulator (5 variants, 500 games each, seeds 50000..50499).
4. Generates updated publication tables and figures.

All outputs are saved to experiments/paper1/runs/paper1_v101_verified/.
Old v1.0.0 production data remains untouched.
"""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.paper1.scripts.common import ExperimentPaths
from experiments.paper1.scripts.generate_plots import (
    plot_fig4_player_scaling,
    plot_fig5_rule_variants,
)
from experiments.paper1.scripts.generate_tables import (
    generate_table4_scaling,
    generate_table5_rule_variants,
)
from experiments.paper1.scripts.run_exp04 import run_exp04
from experiments.paper1.scripts.run_exp05 import run_exp05


def main() -> None:
    t_start = time.time()
    num_workers = 8

    run_dir = ExperimentPaths.RUNS / "paper1_v101_verified"
    print("=" * 80)
    print(f"WHOT-ML PAPER 1 — V1.0.1 RE-RUN (EXP-04a, EXP-04b, EXP-05)")
    print(f"Target run directory: {run_dir}")
    print(f"Parallel worker processes: {num_workers}")
    print("=" * 80)

    ExperimentPaths.set_run_directory(run_dir)

    # 1. Copy unaffected baseline summaries from v1.0.0 verified run
    v100_processed = ExperimentPaths.RUNS / "kaggle_production_20261005_verified" / "processed"
    if v100_processed.exists():
        for fname in [
            "exp01_full_summary.json",
            "exp02_full_summary.json",
            "exp03_full_summary.json",
            "exp06_full_summary.json",
        ]:
            src = v100_processed / fname
            dst = ExperimentPaths.PROCESSED / fname
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)
                print(f"  [Setup] Copied baseline summary: {fname}")

    # 2. Run EXP-04a: RandomLegalAgent scaling (2,500 games)
    print("\n" + "#" * 60)
    print(">>> RUNNING EXP-04a (RandomLegalAgent Scaling)")
    print("#" * 60)
    t0 = time.time()
    exp04a_summary = run_exp04(
        pilot=False,
        dry_run=False,
        config_filename="exp04a_random_scaling.json",
        output_tag="exp04a",
        workers=num_workers,
    )
    print(f"EXP-04a completed in {time.time() - t0:.2f}s")

    # 3. Run EXP-04b: RuleBasedAgent scaling (2,500 games)
    print("\n" + "#" * 60)
    print(">>> RUNNING EXP-04b (RuleBasedAgent Scaling)")
    print("#" * 60)
    t0 = time.time()
    exp04b_summary = run_exp04(
        pilot=False,
        dry_run=False,
        config_filename="exp04b_rule_scaling.json",
        output_tag="exp04b",
        workers=num_workers,
    )
    # Save a copy as exp04 for backward compatibility
    with open(ExperimentPaths.PROCESSED / "exp04_full_summary.json", "w", encoding="utf-8") as f:
        json.dump(exp04b_summary, f, indent=2)
    print(f"EXP-04b completed in {time.time() - t0:.2f}s")

    # 4. Run EXP-05: Rule Variants (2,500 games)
    print("\n" + "#" * 60)
    print(">>> RUNNING EXP-05 (Controlled Rule Variants - Stacking Ablations)")
    print("#" * 60)
    t0 = time.time()
    exp05_summary = run_exp05(
        pilot=False,
        dry_run=False,
        workers=num_workers,
    )
    print(f"EXP-05 completed in {time.time() - t0:.2f}s")

    # 5. Generate Tables
    print("\n" + "#" * 60)
    print(">>> GENERATING UPDATED TABLES")
    print("#" * 60)
    t4a_md, t4a_tex = generate_table4_scaling(pilot=False, suffix="full", tag="exp04a")
    print(f"  Table 4a (RandomLegal): {t4a_md.name}, {t4a_tex.name}")

    t4b_md, t4b_tex = generate_table4_scaling(pilot=False, suffix="full", tag="exp04b")
    print(f"  Table 4b (RuleBased): {t4b_md.name}, {t4b_tex.name}")

    t5_md, t5_tex = generate_table5_rule_variants(pilot=False, suffix="full")
    print(f"  Table 5 (Rule Variants): {t5_md.name}, {t5_tex.name}")

    # 6. Generate Figures
    print("\n" + "#" * 60)
    print(">>> GENERATING UPDATED FIGURES")
    print("#" * 60)
    fig4_path = plot_fig4_player_scaling(pilot=False, suffix="full")
    print(f"  Figure 4: {fig4_path.name}")

    fig5_path = plot_fig5_rule_variants(pilot=False, suffix="full")
    print(f"  Figure 5: {fig5_path.name}")

    # 7. Print Summary Statistics Report
    total_elapsed = time.time() - t_start
    print("\n" + "=" * 80)
    print("WHOT-ML V1.0.1 RE-RUN SUMMARY REPORT")
    print(f"Total Wall-Clock Time: {total_elapsed:.2f}s")
    print("=" * 80)

    # EXP-04a stats
    res4a = exp04a_summary["scaling_results"]
    print("\n[EXP-04a: RandomLegal Scaling]")
    for n in sorted(int(k) for k in res4a.keys()):
        tc = res4a[str(n)]["turn_count"]
        tr = res4a[str(n)]["truncation"]
        print(f"  N={n}: Mean Turns = {tc['mean']:.1f} (std={tc['std']:.1f}), Truncation = {tr['point']:.1%} [{tr['ci_lower']:.1%}, {tr['ci_upper']:.1%}]")

    # EXP-04b stats
    res4b = exp04b_summary["scaling_results"]
    print("\n[EXP-04b: RuleBased Scaling]")
    for n in sorted(int(k) for k in res4b.keys()):
        tc = res4b[str(n)]["turn_count"]
        tr = res4b[str(n)]["truncation"]
        print(f"  N={n}: Mean Turns = {tc['mean']:.1f} (std={tc['std']:.1f}), Truncation = {tr['point']:.1%} [{tr['ci_lower']:.1%}, {tr['ci_upper']:.1%}]")

    # EXP-05 stats
    variants = exp05_summary["variants"]
    print("\n[EXP-05: Controlled Rule Variants]")
    for vid, vdata in variants.items():
        tc = vdata["turn_count"]
        dc = vdata["draw_count"]
        wr = vdata["rule_based_win_rate"]
        tr = vdata["truncation"]
        delta_str = ""
        if vid != "VAR-BASE" and vid in exp05_summary.get("paired_comparisons_vs_base", {}):
            comp = exp05_summary["paired_comparisons_vs_base"][vid]
            delta_str = f" | ΔTurns={comp['turn_diff_stats']['mean']:+.1f}, Cliff's δ={comp['turn_cliffs_delta']:.2f}"
        print(f"  {vid:16s}: Turns={tc['mean']:.1f} | Draws={dc['mean']:.1f} | RuleBased Win={wr['point']:.1%} | Trunc={tr['point']:.1%}{delta_str}")


if __name__ == "__main__":
    main()
