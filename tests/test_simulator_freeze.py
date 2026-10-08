"""Regression and integrity test enforcing strict simulator freeze at commit 7c1a2dc.

Verifies:
1. No files under whot_ml/ have been added, deleted, or modified relative to 7c1a2dc.
2. Git status reports clean working tree for whot_ml/.
3. Version constants match the frozen baseline specification.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from whot_ml.version import BASELINE_ENVIRONMENT, FROZEN_BASELINE, SIMULATOR_VERSION

FROZEN_COMMIT = "7c1a2dc"


def test_frozen_constants() -> None:
    """Verify that version constants declare a frozen baseline."""
    assert SIMULATOR_VERSION == "1.0.0"
    assert BASELINE_ENVIRONMENT == "WHOT-NG-v1.0"
    assert FROZEN_BASELINE is True


def test_whot_ml_tree_is_unmodified_against_frozen_commit() -> None:
    """Verify git diff between HEAD/working tree and frozen commit 7c1a2dc for whot_ml/ is strictly empty."""
    # Check working tree diff against frozen commit
    cmd_diff = ["git", "diff", "--name-only", FROZEN_COMMIT, "--", "whot_ml/"]
    res_diff = subprocess.run(cmd_diff, capture_output=True, text=True, check=True)
    changed_files = res_diff.stdout.strip().splitlines()

    assert len(changed_files) == 0, (
        f"CRITICAL ERROR: Files under whot_ml/ have been modified relative to frozen commit {FROZEN_COMMIT}: "
        f"{changed_files}"
    )

    # Check untracked or staged files in whot_ml/
    cmd_status = ["git", "status", "--porcelain", "--", "whot_ml/"]
    res_status = subprocess.run(cmd_status, capture_output=True, text=True, check=True)
    status_lines = res_status.stdout.strip().splitlines()

    assert len(status_lines) == 0, (
        f"CRITICAL ERROR: Uncommitted changes or untracked files detected in whot_ml/: "
        f"{status_lines}"
    )
