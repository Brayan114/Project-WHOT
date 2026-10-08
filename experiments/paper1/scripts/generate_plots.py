"""Publication-quality figure generation for Paper 1 (Stage 3B).

Generates standardized academic figures directly from processed metrics JSON files.
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

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt

from experiments.paper1.scripts.common import ExperimentPaths


# Styling settings
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9,
    "figure.titlesize": 13,
    "figure.dpi": 300,
})


def plot_fig1_characterization(pilot: bool = True, suffix: Optional[str] = None) -> Path:
    """Figure 1: Environment Characterization (Legal actions and Game duration)."""
    if suffix is None:
        suffix = "pilot" if pilot else "full"
    json_path = ExperimentPaths.PROCESSED / f"exp01_{suffix}_summary.json"
    if not json_path.exists():
        raise FileNotFoundError(f"Missing processed data: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cohorts = data["cohorts"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2))

    # Subplot A: Legal Actions ECDF
    for cname, cdata in cohorts.items():
        ecdf = cdata.get("legal_action_ecdf", [])
        if ecdf:
            xs = [pt["x"] for pt in ecdf]
            ys = [pt["y"] for pt in ecdf]
            lbl = "RandomLegal" if "random" in cname else "RuleBased"
            ax1.step(xs, ys, where="post", label=lbl, linewidth=1.8)

    ax1.set_xlabel("Legal Actions Available $|A(s_t)|$")
    ax1.set_ylabel("Empirical Cumulative Probability")
    ax1.set_title("A: Legal Action Distribution ECDF")
    ax1.set_xlim(0, 25)
    ax1.set_ylim(0, 1.02)
    ax1.legend(loc="lower right")

    # Subplot B: Game Length Distribution Summary
    labels = []
    means = []
    medians = []
    iqr_lowers = []
    iqr_uppers = []

    for cname, cdata in cohorts.items():
        lbl = "RandomLegal" if "random" in cname else "RuleBased"
        tc = cdata["turn_count"]
        labels.append(lbl)
        means.append(tc["mean"])
        medians.append(tc["median"])
        iqr_lowers.append(tc["median"] - tc["q25"])
        iqr_uppers.append(tc["q75"] - tc["median"])

    x = range(len(labels))
    ax2.errorbar(
        x, medians, yerr=[iqr_lowers, iqr_uppers], fmt="o", color="#1f77b4",
        capsize=5, elinewidth=1.8, label="Median (IQR)"
    )
    ax2.scatter(x, means, color="#d62728", marker="x", s=60, label="Mean", zorder=3)
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(labels)
    ax2.set_ylabel("Game Duration (Turns)")
    ax2.set_title("B: Game Duration by Agent Baseline")
    ax2.legend(loc="upper right")

    status_str = "PILOT" if pilot else "FULL"
    fig.suptitle(f"WHOT-NG-v1 Environment Characterization [{status_str}]", y=1.02)
    plt.tight_layout()

    out_path = ExperimentPaths.FIGURES / f"fig1_characterization_{suffix}.png"
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    return out_path


def plot_fig2_partial_observability(pilot: bool = True, suffix: Optional[str] = None) -> Path:
    """Figure 2: Partial Observability Trajectory Divergence Rates."""
    if suffix is None:
        suffix = "pilot" if pilot else "full"
    json_path = ExperimentPaths.PROCESSED / f"exp02_{suffix}_summary.json"
    if not json_path.exists():
        raise FileNotFoundError(f"Missing processed data: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rates = data.get("mode_divergence_rates", {})
    fig, ax = plt.subplots(figsize=(6.5, 4.0))

    modes = list(rates.keys())
    vals = [rates[m] * 100 for m in modes]
    clean_modes = [m.replace("_", " ").title() for m in modes]

    bars = ax.bar(clean_modes, vals, color=["#2ca02c", "#ff7f0e", "#1f77b4"], width=0.55)
    for b in bars:
        h = b.get_height()
        ax.annotate(
            f"{h:.1f}%",
            xy=(b.get_x() + b.get_width() / 2, h),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    ax.set_ylabel("Trajectory Divergence Rate (%)")
    ax.set_ylim(0, 110)
    status_str = suffix.upper()
    ax.set_title(f"Trajectory Divergence Rate from Equivalent States [{status_str}]")
    plt.tight_layout()

    out_path = ExperimentPaths.FIGURES / f"fig2_partial_observability_{suffix}.png"
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    return out_path


def plot_fig3_baseline_winrates(pilot: bool = True, suffix: Optional[str] = None) -> Path:
    """Figure 3: Baseline Agent Win Rates with Wilson Score 95% CIs."""
    if suffix is None:
        suffix = "pilot" if pilot else "full"
    json_path = ExperimentPaths.PROCESSED / f"exp03_{suffix}_summary.json"
    if not json_path.exists():
        raise FileNotFoundError(f"Missing processed data: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    matchups = data["matchups"]
    fig, ax = plt.subplots(figsize=(7.5, 4.2))

    labels = []
    points = []
    yerr_lowers = []
    yerr_uppers = []

    for m_id in ["BRRR", "BR_2P"]:
        if m_id in matchups:
            wr_stats = matchups[m_id]["win_rate_stats"]
            rb_stat = wr_stats.get("rule_based", {})
            labels.append(f"{m_id}\n(RuleBased)")
            pt = rb_stat.get("point", 0.0)
            ci_l = rb_stat.get("ci_lower", 0.0)
            ci_u = rb_stat.get("ci_upper", 0.0)
            points.append(pt)
            yerr_lowers.append(pt - ci_l)
            yerr_uppers.append(ci_u - pt)

    x = range(len(labels))
    bars = ax.bar(x, points, width=0.45, color="#1f77b4", alpha=0.85, label="Win Rate")
    ax.errorbar(
        x, points, yerr=[yerr_lowers, yerr_uppers], fmt="none", ecolor="black",
        capsize=6, elinewidth=1.8, label="95% Wilson CI"
    )

    for i, pt in enumerate(points):
        ax.annotate(
            f"{pt:.1%}",
            xy=(i, pt),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            fontweight="bold",
        )

    ax.axhline(0.25, color="gray", linestyle="--", linewidth=1, label="Expected Random 4P (25%)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylabel("Win Rate")
    ax.set_ylim(0, 1.05)
    status_str = "PILOT" if pilot else "FULL"
    ax.set_title(f"RuleBasedAgent Win Rates in Asymmetric Matchups [{status_str}]")
    ax.legend(loc="upper right")
    plt.tight_layout()

    out_path = ExperimentPaths.FIGURES / f"fig3_baseline_winrates_{suffix}.png"
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    return out_path


def plot_fig4_player_scaling(pilot: bool = True, suffix: Optional[str] = None) -> Path:
    """Figure 4: Player Count Scaling (Game length vs N)."""
    if suffix is None:
        suffix = "pilot" if pilot else "full"
    json_path = ExperimentPaths.PROCESSED / f"exp04_{suffix}_summary.json"
    if not json_path.exists():
        raise FileNotFoundError(f"Missing processed data: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    scaling = data["scaling_results"]
    fig, ax = plt.subplots(figsize=(7.0, 4.2))

    ns = sorted(int(k) for k in scaling.keys())
    total_turns = [scaling[str(n)]["turn_count"]["mean"] for n in ns]
    turns_per_player = [scaling[str(n)]["turns_per_player"]["mean"] for n in ns]

    ax.plot(ns, total_turns, marker="o", linewidth=2, color="#1f77b4", label="Total Game Turns")
    ax.plot(ns, turns_per_player, marker="s", linewidth=2, linestyle="--", color="#2ca02c", label="Turns per Player")

    ax.set_xlabel("Number of Players ($N$)")
    ax.set_ylabel("Mean Turns to Completion")
    ax.set_xticks(ns)
    status_str = suffix.upper()
    ax.set_title(f"Game Duration Scaling across Player Counts $N \\in \\{{2..6\\}}$ [{status_str}]")
    ax.legend(loc="upper left")
    plt.tight_layout()

    out_path = ExperimentPaths.FIGURES / f"fig4_player_scaling_{suffix}.png"
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    return out_path


def plot_fig5_rule_variants(pilot: bool = True, suffix: Optional[str] = None) -> Path:
    """Figure 5: Rule Variant Duration Comparisons."""
    if suffix is None:
        suffix = "pilot" if pilot else "full"
    json_path = ExperimentPaths.PROCESSED / f"exp05_{suffix}_summary.json"
    if not json_path.exists():
        raise FileNotFoundError(f"Missing processed data: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    variants = data["variants"]
    fig, ax = plt.subplots(figsize=(8.0, 4.2))

    v_ids = list(variants.keys())
    means = [variants[v]["turn_count"]["mean"] for v in v_ids]
    stds = [variants[v]["turn_count"]["std"] for v in v_ids]

    bars = ax.bar(v_ids, means, yerr=stds, capsize=5, color="#1f77b4", alpha=0.85, width=0.5)

    for b in bars:
        h = b.get_height()
        ax.annotate(
            f"{h:.1f}",
            xy=(b.get_x() + b.get_width() / 2, h / 2),
            ha="center",
            va="center",
            color="white",
            fontweight="bold",
        )

    ax.set_ylabel("Mean Turns to Completion")
    status_str = suffix.upper()
    ax.set_title(f"Game Duration Comparison across Controlled Rule Variants [{status_str}]")
    plt.tight_layout()

    out_path = ExperimentPaths.FIGURES / f"fig5_rule_variants_{suffix}.png"
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    return out_path


def generate_all_plots(pilot: bool = True, suffix: Optional[str] = None) -> List[Path]:
    """Generate all figures for Paper 1."""
    ExperimentPaths.ensure_directories()
    paths = []
    mode_str = suffix.upper() if suffix else ("PILOT" if pilot else "FULL")
    print(f"\n[PLOTS] Generating publication figures ({mode_str})...")

    p1 = plot_fig1_characterization(pilot=pilot, suffix=suffix)
    paths.append(p1)
    print(f"  Saved: {p1}")

    p2 = plot_fig2_partial_observability(pilot=pilot, suffix=suffix)
    paths.append(p2)
    print(f"  Saved: {p2}")

    p3 = plot_fig3_baseline_winrates(pilot=pilot, suffix=suffix)
    paths.append(p3)
    print(f"  Saved: {p3}")

    p4 = plot_fig4_player_scaling(pilot=pilot, suffix=suffix)
    paths.append(p4)
    print(f"  Saved: {p4}")

    p5 = plot_fig5_rule_variants(pilot=pilot, suffix=suffix)
    paths.append(p5)
    print(f"  Saved: {p5}")

    return paths


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Paper 1 Plots")
    parser.add_argument("--full", action="store_true", help="Generate from full data instead of pilot")
    parser.add_argument("--dry-run", action="store_true", help="Generate from dry-run data")
    args = parser.parse_args()
    suffix_arg = "dry_run" if args.dry_run else ("full" if args.full else "pilot")
    generate_all_plots(pilot=not args.full, suffix=suffix_arg)
