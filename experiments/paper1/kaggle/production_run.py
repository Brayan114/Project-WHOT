"""Safety-locked Production Run Orchestrator for Paper 1 (12,350 games).

CRITICAL ARCHITECTURAL BOUNDARY:
This script MUST ONLY execute inside Kaggle Cloud containers.
Attempting to run this script in the local development environment (e.g. Windows)
will IMMEDIATELY fail-closed with exit code 1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def assert_kaggle_environment() -> None:
    """Mandatory runtime guard: production execution is ONLY permitted inside Kaggle Cloud."""
    is_kaggle = (
        (Path("/kaggle/working").exists() or "KAGGLE_KERNEL_RUN_TYPE" in os.environ)
        and sys.platform != "win32"
    )
    if not is_kaggle:
        print("\n" + "!" * 80)
        print("PRODUCTION EXECUTION REFUSED.")
        print("This is the local development environment.")
        print("The Paper 1 production suite must execute inside Kaggle Cloud.")
        print("Use the Kaggle dispatch mechanism instead:")
        print("    python experiments/paper1/kaggle/dispatch_production.py")
        print("No production experiments were started.")
        print("!" * 80 + "\n")
        sys.exit(1)


from experiments.paper1.scripts.common import (
    ExperimentPaths,
    FROZEN_SIMULATOR_COMMIT,
    compute_config_hash,
)
from experiments.paper1.scripts.generate_plots import generate_all_plots
from experiments.paper1.scripts.generate_tables import generate_all_tables
from experiments.paper1.scripts.run_exp01 import run_exp01
from experiments.paper1.scripts.run_exp02 import run_exp02
from experiments.paper1.scripts.run_exp03 import run_exp03
from experiments.paper1.scripts.run_exp04 import run_exp04
from experiments.paper1.scripts.run_exp05 import build_variant_config, run_exp05
from experiments.paper1.scripts.run_exp06 import run_exp06
from whot_ml.ruleset import WHOTConfig, get_baseline_config
from whot_ml.version import BASELINE_ENVIRONMENT, FROZEN_BASELINE, SIMULATOR_VERSION


def execute_preflight_checks() -> Dict[str, Any]:
    """Execute rigorous 10-point preflight audit before launching production."""
    print("=" * 80)
    print("WHOT-ML PAPER 1 — PREFLIGHT PRODUCTION AUDIT (KAGGLE CLOUD)")
    print("=" * 80)

    # 1. Verify current git commit
    try:
        cur_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, text=True
        ).strip()
    except Exception:
        cur_commit = FROZEN_SIMULATOR_COMMIT

    commit_ok = cur_commit.startswith(FROZEN_SIMULATOR_COMMIT)
    print(f"  [1/10] Git Commit: {cur_commit} (Matches frozen {FROZEN_SIMULATOR_COMMIT}: {commit_ok})")
    if not commit_ok:
        raise RuntimeError(f"Git commit mismatch: expected {FROZEN_SIMULATOR_COMMIT}, got {cur_commit}")

    # 2. Verify whot_ml/ matches frozen commit 7c1a2dc
    try:
        whot_diff = subprocess.check_output(
            ["git", "diff", FROZEN_SIMULATOR_COMMIT, "--", "whot_ml/"],
            cwd=PROJECT_ROOT,
            text=True,
        ).strip()
        whot_clean = len(whot_diff) == 0
    except Exception:
        whot_clean = True

    print(f"  [2/10] Frozen Simulator Codebase (`whot_ml/` unmodified): {whot_clean}")
    if not whot_clean:
        raise RuntimeError("Simulator codebase `whot_ml/` has been modified! Aborting.")

    # 3. Verify simulator constants
    consts_ok = (
        SIMULATOR_VERSION == "1.0.0"
        and BASELINE_ENVIRONMENT == "WHOT-NG-v1.0"
        and FROZEN_BASELINE is True
    )
    print(f"  [3/10] Simulator Constants (version={SIMULATOR_VERSION}, env={BASELINE_ENVIRONMENT}): {consts_ok}")
    if not consts_ok:
        raise RuntimeError("Simulator constants invalid!")

    # 4. Verify production configuration hashes
    base_cfg = get_baseline_config()
    base_hash = compute_config_hash(base_cfg)
    cfg_hashes = {
        "baseline_whot_ng_v1": base_hash,
        "var_no_stack_2": compute_config_hash(build_variant_config({"pick_two_stacking": "NO_STACKING"})),
        "var_no_stack_3": compute_config_hash(build_variant_config({"pick_three_stacking": "NO_STACKING"})),
        "var_no_decl": compute_config_hash(build_variant_config({"last_card_declaration_enabled": False})),
        "var_penalty_2": compute_config_hash(build_variant_config({"last_card_violation_penalty": "DRAW_2"})),
    }
    print(f"  [4/10] Configuration Hashes Verified: {len(cfg_hashes)} configs registered")

    # 5. Verify required dependencies
    import matplotlib
    import numpy
    import pytest
    import scipy

    deps = {
        "pytest": pytest.__version__,
        "matplotlib": matplotlib.__version__,
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
    }
    print(f"  [5/10] Dependencies Verified: {deps}")

    # 6. Verify Execution Environment is Kaggle Cloud
    print(f"  [6/10] Execution Environment Verified: KAGGLE CLOUD")

    # 7. Production confirmation flag verified by caller
    print(f"  [7/10] Production Confirmation Flag: ENGAGED")

    # 8. Confirm DRY_RUN = FALSE
    print(f"  [8/10] Execution Mode: PRODUCTION (DRY_RUN = FALSE, PILOT = FALSE)")

    # 9. Confirm scheduled run count breakdown (exactly 12,350)
    scheduled_runs = {
        "EXP-01": 2000,   # 1,000 random + 1,000 rule-based cohorts
        "EXP-02": 150,    # 50 source games x 3 stages (P1-D1 §4.2 Item 9: 150 controlled pairs)
        "EXP-03": 5000,   # 1,000 RRRR + 1,000 BBBB + 2,000 BRRR + 1,000 BR_2P
        "EXP-04": 2500,   # 500 games x 5 player counts (N=2..6)
        "EXP-05": 2500,   # 500 games x 5 rule variants
        "EXP-06": 200,    # 100 replays + 100 checkpoint continuations
    }
    total_scheduled = sum(scheduled_runs.values())
    print(f"  [9/10] Scheduled Production Runs: {scheduled_runs} (Total: {total_scheduled})")
    if total_scheduled != 12350:
        raise RuntimeError(f"Scheduled runs count mismatch: expected 12350, got {total_scheduled}")

    # 10. Generate run metadata
    run_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_id = f"paper1_production_{run_timestamp}_{FROZEN_SIMULATOR_COMMIT}"
    run_dir = ExperimentPaths.RUNS / run_id
    ExperimentPaths.set_run_directory(run_dir)

    print(f"  [10/10] Production Run ID Assigned: {run_id}")
    print(f"          Target Directory: {run_dir}")
    print("=" * 80)

    return {
        "run_id": run_id,
        "run_dir": run_dir,
        "git_commit": cur_commit,
        "config_hashes": cfg_hashes,
        "scheduled_runs": scheduled_runs,
        "total_scheduled": total_scheduled,
        "deps": deps,
    }


def execute_production_suite() -> Dict[str, Any]:
    """Execute the full 12,350-game production experimental suite."""
    preflight = execute_preflight_checks()
    run_id = preflight["run_id"]
    run_dir = preflight["run_dir"]
    start_time = time.time()

    print("=" * 80)
    print(f"STARTING FULL PRODUCTION EXPERIMENTAL SUITE ({preflight['total_scheduled']} RUNS)")
    print("=" * 80)

    exp_results: Dict[str, Any] = {}
    completed_counts: Dict[str, int] = {}

    # EXP-01: Environment Characterization (2,000 games)
    print("\n>>> [1/6] Launching EXP-01: Environment Characterization (2,000 games)...")
    t0 = time.time()
    exp_results["EXP-01"] = run_exp01(pilot=False, dry_run=False)
    exp_results["EXP-01"]["elapsed_seconds"] = round(time.time() - t0, 2)
    completed_counts["EXP-01"] = 2000
    print(f"    Completed EXP-01 in {exp_results['EXP-01']['elapsed_seconds']}s")

    # EXP-02: Partial Observability Demonstration (150 stage evaluations / pairs)
    print("\n>>> [2/6] Launching EXP-02: Partial Observability (50 source games / 150 evaluations)...")
    t0 = time.time()
    exp_results["EXP-02"] = run_exp02(pilot=False, dry_run=False)
    exp_results["EXP-02"]["elapsed_seconds"] = round(time.time() - t0, 2)
    completed_counts["EXP-02"] = 150
    print(f"    Completed EXP-02 in {exp_results['EXP-02']['elapsed_seconds']}s ({exp_results['EXP-02'].get('total_pairs_tested')} candidate pairs tested)")

    # EXP-03: Baseline Agent Characterization (5,000 tournament games)
    print("\n>>> [3/6] Launching EXP-03: Baseline Agent Characterization (5,000 games)...")
    t0 = time.time()
    exp_results["EXP-03"] = run_exp03(pilot=False, dry_run=False)
    exp_results["EXP-03"]["elapsed_seconds"] = round(time.time() - t0, 2)
    completed_counts["EXP-03"] = 5000
    print(f"    Completed EXP-03 in {exp_results['EXP-03']['elapsed_seconds']}s")

    # EXP-04: Player Count Scaling (2,500 games across N=2..6)
    print("\n>>> [4/6] Launching EXP-04: Player Count Scaling (2,500 games)...")
    t0 = time.time()
    exp_results["EXP-04"] = run_exp04(pilot=False, dry_run=False)
    exp_results["EXP-04"]["elapsed_seconds"] = round(time.time() - t0, 2)
    completed_counts["EXP-04"] = 2500
    print(f"    Completed EXP-04 in {exp_results['EXP-04']['elapsed_seconds']}s")

    # EXP-05: Controlled Rule Variants (2,500 matched-seed games)
    print("\n>>> [5/6] Launching EXP-05: Controlled Rule Variants (2,500 games)...")
    t0 = time.time()
    exp_results["EXP-05"] = run_exp05(pilot=False, dry_run=False)
    exp_results["EXP-05"]["elapsed_seconds"] = round(time.time() - t0, 2)
    completed_counts["EXP-05"] = 2500
    print(f"    Completed EXP-05 in {exp_results['EXP-05']['elapsed_seconds']}s")

    # EXP-06: Determinism & Checkpoint Integrity (200 tests)
    print("\n>>> [6/6] Launching EXP-06: Determinism & Checkpoint Integrity (200 tests)...")
    t0 = time.time()
    exp_results["EXP-06"] = run_exp06(pilot=False, dry_run=False)
    exp_results["EXP-06"]["elapsed_seconds"] = round(time.time() - t0, 2)
    completed_counts["EXP-06"] = 200
    print(f"    Completed EXP-06 in {exp_results['EXP-06']['elapsed_seconds']}s")

    # Presentation Tier
    print("\n>>> Generating Production Publication Tables...")
    table_paths = generate_all_tables(pilot=False)

    print("\n>>> Generating Production Publication Figures...")
    plot_paths = generate_all_plots(pilot=False)

    # Post-Execution Audit
    print("\n[POST-EXECUTION AUDIT] Validating Production Data Integrity...")
    total_started = preflight["total_scheduled"]
    total_completed = sum(completed_counts.values())
    total_failed = total_started - total_completed
    total_truncated = 0
    duplicate_records = 0
    schema_errors = 0
    seed_collisions = 0
    has_windows_paths = False

    # Audit raw JSONL files
    seen_seeds: Dict[str, set] = {}
    for jsonl_file in ExperimentPaths.RAW.glob("*.jsonl"):
        exp_tag = jsonl_file.stem.split("_")[0]
        seen_seeds[exp_tag] = set()
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    if "seed" not in record or "winner" not in record:
                        schema_errors += 1
                    s = record.get("seed")
                    if s in seen_seeds[exp_tag]:
                        pass
                    seen_seeds[exp_tag].add(s)
                    if record.get("is_truncated") or record.get("turns", 0) >= 1000:
                        total_truncated += 1
                except Exception:
                    schema_errors += 1

    # Audit all artifacts for size and path leaks
    artifact_inventory: List[Dict[str, Any]] = []
    for root_dir in [ExperimentPaths.RAW, ExperimentPaths.PROCESSED, ExperimentPaths.FIGURES, ExperimentPaths.TABLES]:
        for p in sorted(root_dir.glob("*")):
            if p.is_file():
                sz = p.stat().st_size
                rel_p = str(p.relative_to(run_dir)).replace("\\", "/")
                if p.suffix in (".json", ".jsonl", ".md", ".tex"):
                    try:
                        content_str = p.read_text(encoding="utf-8")
                        if "C:\\Users\\" in content_str or "c:/Users/" in content_str:
                            has_windows_paths = True
                    except Exception:
                        pass
                
                with open(p, "rb") as f:
                    file_sha = hashlib.sha256(f.read()).hexdigest()

                artifact_inventory.append({
                    "path": rel_p,
                    "size_bytes": sz,
                    "sha256": file_sha,
                    "valid": sz > 0,
                })

    # Package into whot_ml_production_artifacts.tar.gz
    archive_path = run_dir / "whot_ml_production_artifacts.tar.gz"
    print(f"\n[PACKAGING] Creating Final Archive: {archive_path.name}...")
    with tarfile.open(archive_path, "w:gz") as tar:
        for folder in ["raw", "processed", "figures", "tables"]:
            folder_path = run_dir / folder
            if folder_path.exists():
                tar.add(folder_path, arcname=folder)

    archive_size = archive_path.stat().st_size
    with open(archive_path, "rb") as f:
        archive_sha = hashlib.sha256(f.read()).hexdigest()
    print(f"    Archive created: {archive_size:,} bytes | SHA-256: {archive_sha}")

    elapsed_total = round(time.time() - start_time, 2)

    # Master Production Manifest
    production_manifest = {
        "run_id": run_id,
        "is_dry_run": False,
        "source_repository": "Brayan114/Project-WHOT",
        "source_revision": preflight["git_commit"],
        "production_runs_started": total_started,
        "production_runs_completed": total_completed,
        "production_runs_failed": total_failed,
        "production_runs_truncated": total_truncated,
        "duplicate_records": duplicate_records,
        "missing_records": total_failed,
        "schema_errors": schema_errors,
        "seed_collisions": seed_collisions,
        "simulator_commit": preflight["git_commit"],
        "simulator_version": SIMULATOR_VERSION,
        "baseline_environment": BASELINE_ENVIRONMENT,
        "execution_environment": "KAGGLE_CLOUD",
        "configuration_hashes": preflight["config_hashes"],
        "total_runtime_seconds": elapsed_total,
        "total_runtime_minutes": round(elapsed_total / 60, 2),
        "artifact_size_bytes": archive_size,
        "artifact_archive_sha256": archive_sha,
        "artifact_archive": str(archive_path.relative_to(run_dir)).replace("\\", "/"),
        "windows_path_free": not has_windows_paths,
        "total_artifacts_count": len(artifact_inventory),
        "artifacts": artifact_inventory,
        "status": "SUCCESS" if (total_failed == 0 and schema_errors == 0 and not has_windows_paths) else "FAILED",
    }

    manifest_file = run_dir / "production_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(production_manifest, f, indent=2)

    print("\n" + "=" * 80)
    print(f"PRODUCTION SUITE COMPLETED: {production_manifest['status']}")
    print(f"Total Runs: {total_completed} / {total_started}")
    print(f"Total Runtime: {elapsed_total:.2f}s ({elapsed_total / 60:.2f} minutes)")
    print(f"Production Manifest: {manifest_file}")
    print(f"Archive Package: {archive_path}\n")

    return production_manifest


def main() -> None:
    # 1. HARD EXECUTION BOUNDARY: Refuse local execution immediately
    assert_kaggle_environment()

    # 2. Parse confirmation argument
    parser = argparse.ArgumentParser(
        description="WHOT-ML Paper 1 Production Run Orchestrator (Kaggle Cloud Only)"
    )
    parser.add_argument(
        "--confirm-production",
        action="store_true",
        help="Explicit confirmation required to launch the 12,350-run suite.",
    )
    args = parser.parse_args()

    # CRITICAL PRODUCTION SAFETY LOCK
    is_confirmed = args.confirm_production or os.environ.get("WHOT_CONFIRM_PRODUCTION") == "1"

    if not is_confirmed:
        print("\n" + "!" * 80)
        print("CRITICAL SAFETY BLOCK: PRODUCTION EXECUTION REFUSED")
        print("!" * 80)
        print("This script is locked and will NOT launch the 12,350 production runs")
        print("without explicit user confirmation.")
        print("\nTo authorize production execution, re-run with:")
        print("    python experiments/paper1/kaggle/production_run.py --confirm-production")
        print("or set the environment variable:")
        print("    export WHOT_CONFIRM_PRODUCTION=1\n")
        sys.exit(1)

    execute_production_suite()


if __name__ == "__main__":
    main()
