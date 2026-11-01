"""Regression and integrity test enforcing strict simulator freeze at commit 7c1a2dc and v1.0.1 release boundary.

Verifies:
1. Only allowed bug-fix files under whot_ml/ have been modified relative to 7c1a2dc (rules_engine.py and version.py).
2. Git status reports no unexpected untracked or modified files in whot_ml/.
3. Version constants match the v1.0.1 specification.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from whot_ml.version import BASELINE_ENVIRONMENT, FROZEN_BASELINE, SIMULATOR_VERSION

FROZEN_COMMIT = "7c1a2dc"
ALLOWED_MODIFIED_FILES = {"whot_ml/rules_engine.py", "whot_ml/version.py"}


def test_frozen_constants() -> None:
    """Verify that version constants declare a frozen baseline with v1.0.1."""
    assert SIMULATOR_VERSION == "1.0.1"
    assert BASELINE_ENVIRONMENT == "WHOT-NG-v1.0"
    assert FROZEN_BASELINE is True


def test_whot_ml_tree_is_unmodified_against_frozen_commit() -> None:
    """Verify git diff between HEAD/working tree and frozen commit 7c1a2dc for whot_ml/ contains only allowed v1.0.1 fixes."""
    # Check working tree diff against frozen commit
    cmd_diff = ["git", "diff", "--name-only", FROZEN_COMMIT, "--", "whot_ml/"]
    res_diff = subprocess.run(cmd_diff, capture_output=True, text=True, check=True)
    changed_files = [f.replace("\\", "/") for f in res_diff.stdout.strip().splitlines() if f.strip()]

    assert set(changed_files) == ALLOWED_MODIFIED_FILES, (
        f"CRITICAL ERROR: Changed files under whot_ml/ relative to {FROZEN_COMMIT} "
        f"do not match expected v1.0.1 release files ({ALLOWED_MODIFIED_FILES}): {changed_files}"
    )

    # Check untracked or staged files in whot_ml/
    cmd_status = ["git", "status", "--porcelain", "--", "whot_ml/"]
    res_status = subprocess.run(cmd_status, capture_output=True, text=True, check=True)
    status_lines = res_status.stdout.strip().splitlines()
    status_files = {
        line.split(maxsplit=1)[1].strip().replace("\\", "/")
        for line in status_lines
        if line.strip() and len(line.split(maxsplit=1)) > 1
    }

    assert status_files.issubset(ALLOWED_MODIFIED_FILES), (
        f"CRITICAL ERROR: Unexpected uncommitted or untracked files detected in whot_ml/: "
        f"{status_files - ALLOWED_MODIFIED_FILES}"
    )
