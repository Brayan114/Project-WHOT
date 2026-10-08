# WHOT-ML Paper 1 Experimental Suite

This directory contains the complete, reproducible experimental apparatus for Paper 1:

> **“WHOT-ML: A Configurable Partially Observable Multi-Agent Environment for Machine Learning Research.”**

The underlying simulator baseline `WHOT-NG-v1.0` (commit `7c1a2dc`) is completely frozen and serves as the laboratory instrument. All measurement, telemetry, statistical aggregation, plotting, and reporting tools wrap the simulator externally.

---

## Directory Layout

```text
experiments/paper1/
├── configs/              # Experiment configuration JSON files (EXP-01 to EXP-06)
├── scripts/              # Python implementation modules
│   ├── common.py         # Shared telemetry, manifest, seat balancing, and statistics
│   ├── run_exp01.py      # EXP-01 Environment Characterization
│   ├── run_exp02.py      # EXP-02 Partial Observability Demonstration
│   ├── run_exp03.py      # EXP-03 Baseline Agent Tournament
│   ├── run_exp04.py      # EXP-04 Player Count Scaling (N in 2..6)
│   ├── run_exp05.py      # EXP-05 Controlled Rule Variants
│   ├── run_exp06.py      # EXP-06 Event-Level Determinism & Checkpointing
│   ├── generate_plots.py # Publication-quality figure generation (PNG)
│   └── generate_tables.py# LaTeX (.tex) and Markdown (.md) table generator
├── raw/                  # Raw JSONL / JSON trajectory traces and event logs
├── processed/            # Derived metrics, aggregated statistics, and CIs
├── figures/              # Publication figures
├── tables/               # LaTeX and Markdown summary tables
├── reports/              # Markdown execution logs
├── run_experiments.py    # Unified CLI entrypoint
└── README.md             # This document
```

---

## Reproduction Instructions

### 1. Run Verification Tests
Verify that the test suite passes (including 96 existing tests and all new Paper 1 apparatus tests):
```powershell
pytest
```

### 2. Execute Pilot Runs (Validation of Apparatus)
To run small-scale pilot executions of all experiments and automatically generate figures and tables:
```powershell
python experiments/paper1/run_experiments.py --experiment all --pilot
```

To run individual experiments:
```powershell
python experiments/paper1/scripts/run_exp01.py
python experiments/paper1/scripts/run_exp02.py
python experiments/paper1/scripts/run_exp03.py
python experiments/paper1/scripts/run_exp04.py
python experiments/paper1/scripts/run_exp05.py
python experiments/paper1/scripts/run_exp06.py
```

### 3. Generate Presentation Artifacts
To regenerate figures and tables from processed metrics:
```powershell
python experiments/paper1/scripts/generate_plots.py
python experiments/paper1/scripts/generate_tables.py
```

### 4. Execute Full-Scale Experiments
*Note: Run only after the measuring apparatus has been audited and approved.*
```powershell
python experiments/paper1/run_experiments.py --experiment all --full
```
