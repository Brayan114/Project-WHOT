"""Environment, Git, and Simulator Freeze Verification for Kaggle Deployment.

Audits runtime environment, system specs, dependency versions, git commit,
and executes the complete test suite (109 tests) to verify apparatus readiness.
Strictly adheres to security policies: NO credentials or tokens are ever logged or printed.
"""

from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.paper1.scripts.common import FROZEN_SIMULATOR_COMMIT
from whot_ml.version import BASELINE_ENVIRONMENT, FROZEN_BASELINE, SIMULATOR_VERSION


def check_kaggle_auth() -> bool:
    """Perform a harmless authenticated Kaggle API check without exposing secrets."""
    try:
        # Run harmless command: kaggle kernels list -m --page 1
        res = subprocess.run(
            ["kaggle", "kernels", "list", "-m", "--page", "1"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return res.returncode == 0
    except Exception:
        return False


def get_git_info() -> Dict[str, Any]:
    """Inspect Git commit and working tree state for whot_ml/."""
    try:
        commit_res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=PROJECT_ROOT,
        )
        current_commit = commit_res.stdout.strip()
    except Exception as e:
        current_commit = f"ERROR: {e}"

    try:
        diff_res = subprocess.run(
            ["git", "diff", "--name-only", FROZEN_SIMULATOR_COMMIT, "--", "whot_ml/"],
            capture_output=True,
            text=True,
            check=True,
            cwd=PROJECT_ROOT,
        )
        whot_ml_diff = [line.strip() for line in diff_res.stdout.splitlines() if line.strip()]
    except Exception as e:
        whot_ml_diff = [f"ERROR: {e}"]

    try:
        status_res = subprocess.run(
            ["git", "status", "--porcelain", "--", "whot_ml/"],
            capture_output=True,
            text=True,
            check=True,
            cwd=PROJECT_ROOT,
        )
        whot_ml_status = [line.strip() for line in status_res.stdout.splitlines() if line.strip()]
    except Exception as e:
        whot_ml_status = [f"ERROR: {e}"]

    return {
        "current_commit": current_commit,
        "frozen_reference_commit": FROZEN_SIMULATOR_COMMIT,
        "commit_matches_frozen": current_commit.startswith(FROZEN_SIMULATOR_COMMIT),
        "whot_ml_diff_files": whot_ml_diff,
        "whot_ml_uncommitted_files": whot_ml_status,
        "whot_ml_clean": len(whot_ml_diff) == 0 and len(whot_ml_status) == 0,
    }


def get_package_versions() -> Dict[str, str]:
    """Capture exact installed package versions for dependency reproducibility."""
    target_pkgs = ["pytest", "matplotlib", "numpy", "scipy", "kaggle", "setuptools"]
    versions = {}
    for pkg in target_pkgs:
        try:
            versions[pkg] = importlib.metadata.version(pkg)
        except Exception:
            versions[pkg] = "not-installed"
    return versions


def run_test_suite() -> Dict[str, Any]:
    """Execute pytest on tests/ and capture pass/fail counts."""
    cmd = [sys.executable, "-m", "pytest", "-q", "--tb=short"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=120)
        output = res.stdout.strip()
        passed = "109 passed" in output
        return {
            "returncode": res.returncode,
            "passed": passed,
            "summary_line": output.splitlines()[-1] if output else "No output",
            "all_tests_passed": res.returncode == 0 and passed,
        }
    except Exception as e:
        return {
            "returncode": -1,
            "passed": False,
            "summary_line": f"Execution error: {e}",
            "all_tests_passed": False,
        }


def run_environment_audit(output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Perform full environment audit and emit manifest."""
    print("=" * 70)
    print("WHOT-ML — Environment & Deployment Audit")
    print("=" * 70)

    # 1. System info
    sys_info = {
        "os": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python_version": sys.version.split()[0],
        "python_executable": sys.executable,
        "cpu_count": os.cpu_count() or 1,
    }
    print(f"System: {sys_info['os']} ({sys_info['architecture']}) | Python {sys_info['python_version']}")
    print(f"CPU count: {sys_info['cpu_count']}")

    # 2. Kaggle authentication
    kaggle_auth = check_kaggle_auth()
    auth_status_str = "SUCCESS" if kaggle_auth else "FAILED (or unavailable)"
    print(f"Kaggle authentication: {auth_status_str}")

    # 3. Git & Simulator freeze
    git_info = get_git_info()
    print(f"Current Commit: {git_info['current_commit'][:7]}")
    print(f"Frozen Simulator Commit: {git_info['frozen_reference_commit']}")
    print(f"Simulator core (whot_ml/) untouched: {git_info['whot_ml_clean']}")

    # 4. Version constants
    constants_valid = (
        SIMULATOR_VERSION == "1.0.0"
        and BASELINE_ENVIRONMENT == "WHOT-NG-v1.0"
        and FROZEN_BASELINE is True
    )
    print(f"Simulator Version: {SIMULATOR_VERSION} ({BASELINE_ENVIRONMENT}) | Frozen: {FROZEN_BASELINE}")

    # 5. Dependency versions
    pkg_versions = get_package_versions()
    print(f"Pinned packages: {pkg_versions}")

    # 6. Test suite
    print("Running full pytest suite (tests/)...")
    test_res = run_test_suite()
    print(f"Test suite result: {test_res['summary_line']}")

    # Overall verdict
    is_ready = (
        git_info["whot_ml_clean"]
        and constants_valid
        and test_res["all_tests_passed"]
    )
    print("-" * 70)
    print(f"Deployment Verification Verdict: {'PASS' if is_ready else 'FAIL'}")
    print("=" * 70)

    manifest = {
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "system_info": sys_info,
        "kaggle_authentication_success": kaggle_auth,
        "git_info": git_info,
        "simulator_constants": {
            "simulator_version": SIMULATOR_VERSION,
            "baseline_environment": BASELINE_ENVIRONMENT,
            "frozen_baseline": FROZEN_BASELINE,
            "constants_valid": constants_valid,
        },
        "package_versions": pkg_versions,
        "test_suite": test_res,
        "deployment_ready": is_ready,
    }

    dest_dir = output_dir or PROJECT_ROOT / "experiments" / "paper1" / "kaggle"
    dest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = dest_dir / "environment_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Saved environment manifest: {manifest_path}")
    return manifest


if __name__ == "__main__":
    audit_res = run_environment_audit()
    sys.exit(0 if audit_res["deployment_ready"] else 1)
