"""Unified CLI Runner for WHOT-ML Paper 1 Experiments (Stage 3B).

Usage:
  python run_experiments.py --experiment all --pilot
  python run_experiments.py --experiment exp01 --pilot
  python run_experiments.py --plots --tables --pilot
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import List

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.paper1.scripts.generate_plots import generate_all_plots
from experiments.paper1.scripts.generate_tables import generate_all_tables
from experiments.paper1.scripts.run_exp01 import run_exp01
from experiments.paper1.scripts.run_exp02 import run_exp02
from experiments.paper1.scripts.run_exp03 import run_exp03
from experiments.paper1.scripts.run_exp04 import run_exp04
from experiments.paper1.scripts.run_exp05 import run_exp05
from experiments.paper1.scripts.run_exp06 import run_exp06


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Unified Experiment Runner for Paper 1"
    )
    parser.add_argument(
        "--experiment",
        choices=["all", "exp01", "exp02", "exp03", "exp04", "exp05", "exp06"],
        default="all",
        help="Experiment to execute (default: all)",
    )
    parser.add_argument(
        "--pilot",
        action="store_true",
        default=True,
        help="Run pilot-scale configuration (default: True)",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run rapid 5-game verification smoke test of EXP-01",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full-scale experiment suite (overrides --pilot)",
    )
    parser.add_argument(
        "--plots",
        action="store_true",
        help="Generate publication plots from processed data",
    )
    parser.add_argument(
        "--tables",
        action="store_true",
        help="Generate markdown and LaTeX tables from processed data",
    )
    args = parser.parse_args()

    if args.smoke_test:
        print("=" * 70)
        print(" WHOT-ML Paper 1 Smoke Test (5 games)")
        print("=" * 70)
        start_time = time.time()
        run_exp01(pilot=True, dry_run=True)
        elapsed = time.time() - start_time
        print(f"\n[SUCCESS] Smoke test completed cleanly in {elapsed:.2f} seconds.")
        return

    pilot_mode = not args.full
    status_label = "PILOT" if pilot_mode else "FULL"
    exp_target = args.experiment

    print("=" * 70)
    print(f" WHOT-ML Paper 1 Experiment Runner [{status_label} MODE]")
    print(f" Target: {exp_target}")
    print("=" * 70)

    start_time = time.time()

    if exp_target in ("all", "exp01"):
        run_exp01(pilot=pilot_mode)

    if exp_target in ("all", "exp02"):
        run_exp02(pilot=pilot_mode)

    if exp_target in ("all", "exp03"):
        run_exp03(pilot=pilot_mode)

    if exp_target in ("all", "exp04"):
        run_exp04(pilot=pilot_mode)

    if exp_target in ("all", "exp05"):
        run_exp05(pilot=pilot_mode)

    if exp_target in ("all", "exp06"):
        run_exp06(pilot=pilot_mode)

    if args.plots or exp_target == "all":
        try:
            generate_all_plots(pilot=pilot_mode)
        except Exception as e:
            print(f"[WARNING] Could not generate all plots: {e}")

    if args.tables or exp_target == "all":
        try:
            generate_all_tables(pilot=pilot_mode)
        except Exception as e:
            print(f"[WARNING] Could not generate all tables: {e}")

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f" Run Completed in {elapsed:.2f} seconds.")
    print("=" * 70)


if __name__ == "__main__":
    main()
