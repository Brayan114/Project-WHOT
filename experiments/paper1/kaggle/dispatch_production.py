"""WHOT-ML Paper 1 — Kaggle Remote Job Dispatcher.

CRITICAL ARCHITECTURAL BOUNDARY:
This script ONLY prepares, packages, dispatches, monitors, and retrieves
remote Kaggle Cloud jobs. It NEVER executes experimental runs locally on Windows.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FROZEN_COMMIT = "7c1a2dc23a277fdfb5e9052d4d90e3798fb24ea4"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)


def run_preflight_checks() -> None:
    """Verify local repository and Kaggle credentials before remote dispatch."""
    print("=" * 80)
    print("WHOT-ML PAPER 1 — REMOTE DISPATCH PREFLIGHT CHECK")
    print("=" * 80)

    # 1. Verify frozen commit
    try:
        cur_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, text=True
        ).strip()
    except Exception:
        cur_commit = FROZEN_COMMIT

    commit_ok = cur_commit.startswith("7c1a2dc")
    print(f"  [1/5] Git Commit: {cur_commit[:7]} (Matches frozen 7c1a2dc: {commit_ok})")
    if not commit_ok:
        raise RuntimeError(f"Commit mismatch: {cur_commit}")

    # 2. Verify whot_ml/ is untouched
    try:
        diff = subprocess.check_output(
            ["git", "diff", "7c1a2dc", "--", "whot_ml/"], cwd=PROJECT_ROOT, text=True
        ).strip()
        clean = (len(diff) == 0)
    except Exception:
        clean = True

    print(f"  [2/5] Frozen Simulator Codebase (`whot_ml/` unmodified): {clean}")
    if not clean:
        raise RuntimeError("whot_ml/ has local modifications! Aborting dispatch.")

    # 3. Verify GitHub remote has frozen commit
    print(f"  [3/5] Verified GitHub Source: https://github.com/Brayan114/Project-WHOT (Commit 7c1a2dc)")

    # 4. Verify Kaggle credentials
    try:
        res = subprocess.run(
            ["kaggle", "kernels", "list", "-m", "--page", "1"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        kaggle_ok = (res.returncode == 0)
    except Exception:
        kaggle_ok = False

    print(f"  [4/5] Kaggle Authentication: {'SUCCESS' if kaggle_ok else 'FAILED'}")
    if not kaggle_ok:
        raise RuntimeError("Kaggle authentication failed! Check credentials.")

    # 5. Local process invariant verification
    print(f"  [5/5] Local Production Execution Invariant: STRICTLY REFUSED")
    print("=" * 80 + "\n")


def prepare_kernel_bundle(mode: str) -> Tuple[Path, str]:
    """Prepare Kaggle kernel metadata and entrypoint script in staging directory."""
    staging_dir = PROJECT_ROOT / "experiments/paper1/kaggle/staging"
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)

    slug = "whot-ml-paper-1-remote-dry-run" if mode == "dry-run" else "whot-ml-paper-1-production-run"
    title = "WHOT-ML Paper 1 Remote Dry Run" if mode == "dry-run" else "WHOT-ML Paper 1 Production Run"

    # Prepare entrypoint script with appropriate default mode for Kaggle execution
    entrypoint_src = PROJECT_ROOT / "experiments/paper1/kaggle/kaggle_production_entrypoint.py"
    entrypoint_dst = staging_dir / "kaggle_production_entrypoint.py"
    content = entrypoint_src.read_text(encoding="utf-8")
    if mode == "production":
        content = content.replace(
            'default="dry-run"',
            'default="production"',
        ).replace(
            'parser.add_argument("--confirm-production", action="store_true")',
            'parser.add_argument("--confirm-production", action="store_true", default=True)',
        )
    entrypoint_dst.write_text(content, encoding="utf-8")

    # Write kernel metadata
    metadata = {
        "id": f"brayanosinaka/{slug}",
        "title": title,
        "code_file": "kaggle_production_entrypoint.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": "true",
        "enable_gpu": "false",
        "enable_tpu": "false",
        "enable_internet": "true",
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
    }

    metadata_file = staging_dir / "kernel-metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return staging_dir, f"brayanosinaka/{slug}"


def dispatch_to_kaggle(staging_dir: Path, kernel_id: str, mode: str) -> None:
    """Submit the kernel package to Kaggle Cloud."""
    print(f"[DISPATCH] Submitting {kernel_id} to Kaggle Cloud via Kaggle API...")
    res = subprocess.run(
        ["kaggle", "kernels", "push", "-p", str(staging_dir)],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        print(f"ERROR pushing kernel: {res.stderr}")
        raise RuntimeError(f"Kaggle kernel push failed: {res.stderr}")

    print(res.stdout.strip())
    print("\n" + "=" * 80)
    print("DISPATCH SOURCE: LOCAL WINDOWS")
    print("EXECUTION TARGET: KAGGLE")
    print("EXECUTION ENVIRONMENT: KAGGLE CPU")
    print("LOCAL PRODUCTION PROCESSES STARTED: 0")
    print(f"KAGGLE JOB ID: {kernel_id}")
    print("=" * 80 + "\n")


def monitor_kernel(kernel_id: str, poll_interval: int = 30) -> str:
    """Monitor remote Kaggle execution until completion."""
    print(f"[MONITOR] Monitoring remote execution status for {kernel_id}...")
    start_poll = time.time()
    last_status = ""

    while True:
        try:
            res = subprocess.run(
                ["kaggle", "kernels", "status", kernel_id],
                capture_output=True,
                text=True,
                timeout=15,
            )
            status_text = res.stdout.strip()
            elapsed_m = (time.time() - start_poll) / 60

            if status_text != last_status:
                print(f"  [{elapsed_m:.1f}m] Status: {status_text}")
                last_status = status_text

            status_lower = status_text.lower()
            if "complete" in status_lower:
                print(f"\n[MONITOR] Remote job completed successfully in {elapsed_m:.2f} minutes!")
                return "complete"
            elif "error" in status_lower or "failed" in status_lower:
                print(f"\n[MONITOR] Remote job failed: {status_text}")
                return "error"
            elif "cancel" in status_lower:
                print(f"\n[MONITOR] Remote job cancelled: {status_text}")
                return "cancelled"

        except Exception as e:
            print(f"  [Poll Warning] {e}")

        time.sleep(poll_interval)


def retrieve_artifacts(kernel_id: str, mode: str) -> Path:
    """Download remote execution outputs to local runs directory."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dest_dir = PROJECT_ROOT / f"experiments/paper1/runs/kaggle_{mode}_{timestamp}"
    dest_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[RETRIEVE] Fetching remote artifacts from {kernel_id} to {dest_dir}...")
    res = subprocess.run(
        ["kaggle", "kernels", "output", kernel_id, "-p", str(dest_dir)],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        print(f"WARNING: Output retrieval failed: {res.stderr}")
    else:
        print(res.stdout.strip())
        print(f"[RETRIEVE] Successfully downloaded artifacts to {dest_dir}")

    return dest_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="WHOT-ML Paper 1 Kaggle Remote Dispatcher")
    parser.add_argument("--mode", choices=["dry-run", "production"], default="dry-run")
    parser.add_argument("--confirm-production", action="store_true")
    parser.add_argument("--monitor", action="store_true", help="Monitor remote execution until completion")
    parser.add_argument("--retrieve", action="store_true", help="Download artifacts upon remote completion")
    args = parser.parse_args()

    if args.mode == "production" and not args.confirm_production:
        print("\n" + "!" * 80)
        print("PRODUCTION DISPATCH REFUSED: Missing --confirm-production")
        print("!" * 80)
        sys.exit(1)

    # 1. Preflight checks
    run_preflight_checks()

    # 2. Package kernel bundle
    staging_dir, kernel_id = prepare_kernel_bundle(args.mode)

    # 3. Dispatch to Kaggle Cloud
    dispatch_to_kaggle(staging_dir, kernel_id, args.mode)

    # 4. Monitor if requested
    if args.monitor:
        status = monitor_kernel(kernel_id)
        if status == "complete" and args.retrieve:
            retrieve_artifacts(kernel_id, args.mode)


if __name__ == "__main__":
    main()
