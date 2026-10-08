# WHOT-ML — Paper 1 Kaggle Execution & Deployment Infrastructure

This directory provides the reproducible execution, verification, and deployment wrappers for running the WHOT-ML Paper 1 experimental apparatus on Kaggle (or any standard Linux container).

---

## 1. Core Principles & Freeze Guarantees

1. **Frozen Baseline Simulator:**
   - Simulator version: `1.0.0`
   - Baseline environment: `WHOT-NG-v1`
   - Frozen commit: `7c1a2dc`
   - The simulator code in `whot_ml/` is strictly frozen and never modified.
2. **Unified Code Path:**
   - Kaggle execution uses the exact same runners, telemetry collection, ruleset engine, and statistical routines as local execution.
   - The distinction between dry run, pilot, and production is strictly determined by configuration parameters, not divergent code paths.
3. **Incremental Streaming Persistence:**
   - Raw trajectory telemetry is streamed incrementally to disk (`.jsonl`), ensuring that timeout or container interruptions never destroy previously completed experimental data.
4. **Environment-Agnostic Paths:**
   - All filesystem operations are repository-relative or dynamically resolved; no hard-coded Windows paths exist.
5. **Strict Credential Isolation:**
   - Credentials (e.g. Kaggle API tokens) are NEVER logged, printed, serialized into manifests, committed to git, or bundled into data artifacts.

---

## 2. Directory Structure

```text
experiments/paper1/
  configs/                  # Formal P1-D1 experimental configurations
  scripts/
    common.py               # Shared telemetry, seat rotation, paths, statistics
    run_exp01.py            # EXP-01 Environment Characterization runner
    run_exp02.py            # EXP-02 Partial Observability runner
    run_exp03.py            # EXP-03 Baseline Agent Characterization runner
    run_exp04.py            # EXP-04 Player Count Scaling runner
    run_exp05.py            # EXP-05 Controlled Rule Variants runner
    run_exp06.py            # EXP-06 Determinism & Checkpoint runner
    generate_tables.py      # LaTeX and Markdown table generator
    generate_plots.py       # Publication-quality figure generator
  kaggle/
    README.md               # This deployment guide
    environment_check.py    # Autonomous environment, freeze, and test suite audit
    kaggle_dry_run.py       # End-to-end dry-run pipeline across EXP-01..EXP-06
    production_run.py       # Safety-locked production orchestrator for 12,350 runs
  runs/                     # Isolated output directory for timestamped executions
```

---

## 3. Deployment & Execution Workflows

### Step 1: Pre-Execution Environment Verification
Audit the operating system, Python runtime, simulator freeze, and run all 109 unit tests:
```bash
python experiments/paper1/kaggle/environment_check.py
```
This produces `environment_manifest.json` detailing system specifications and verification status.

### Step 2: Kaggle Dry Run
Execute small-scale runs of all 6 experiments to validate data streaming, serialization, tables, figures, and bitwise determinism:
```bash
python experiments/paper1/kaggle/kaggle_dry_run.py
```
Artifacts will be written to:
`experiments/paper1/runs/paper1_dryrun_<timestamp>_<sha>/`
and packaged into `whot_ml_dryrun_artifacts.tar.gz`.

### Step 3: Production Run (Locked by Default)
The full 12,350-game production suite requires explicit authorization. Merely invoking the script will abort:
```bash
# This will safely refuse to execute:
python experiments/paper1/kaggle/production_run.py

# To explicitly authorize production execution:
python experiments/paper1/kaggle/production_run.py --confirm-production
```

---

## 4. Production Run Architecture: Option A (Single Consolidated Job)

The production suite is executed as a **single consolidated Kaggle CPU notebook/job** rather than fragmented multi-job batches:
- **Projected Total Runtime:** ~46 minutes on modern CPU.
- **Kaggle CPU Time Limit:** 12 hours (720 minutes). The experiment consumes < 7% of available runtime.
- **Benefits:** Eliminates inter-kernel synchronization overhead, maintains unified seed provenance, and produces a single master manifest.
- **Fault-Tolerance:** Each experiment streams records incrementally as games finish. If interrupted, all completed experiments remain safely stored on disk.
