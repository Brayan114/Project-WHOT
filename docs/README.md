# WHOT-ML — Scientific Specifications & Audit Records

This directory contains the formal experimental protocols, claims freeze specifications, and independent scientific audit records supporting the research manuscript **"WHOT-ML: A Configurable Partially Observable Multi-Agent Environment for Machine Learning Research"** and the accompanying Zenodo research artifact.

---

## Directory Contents

### 1. Experimental Protocol & Claims Freeze
- **`WHOT-ML — P1-D1_ Paper 1 Experimental Specification v0.1.md`**  
  Complete experimental protocol governing EXP-01 (Environment Characterization), EXP-02 (Hidden-State Uncertainty), EXP-03 (Baseline Tournament), EXP-04 (Player Scaling), EXP-05 (Rule Ablations), and EXP-06 (Bitwise Reproducibility). Serves as the formal pre-registration document for all production experiments.
- **`P1-D2 — Paper 1 Results & Claims Freeze v0.1.md`**  
  Formal results and claims freeze document capturing the authoritative numerical values for Tables 1–6 and Figures 1–5, establishing the 3-tier claim hierarchy, and enumerating the 12 prohibited claim invariants prior to manuscript composition.

### 2. Independent Scientific Audits
- **`P1-Production-Scientific-Audit-v0.1.md`**  
  Independent statistical audit of the full 12,350-game Kaggle Cloud production campaign (`paper1_production_20261004_215724_7c1a2dc`). Reconstructs all published metrics directly from raw streaming telemetry and verifies zero errors, zero seed collisions, and zero information leakage.
- **`P1-Manuscript-Scientific-Audit-v0.1.md`**  
  Verification audit of `WHOT-ML Paper 1 — Manuscript v1.0.md`. Confirms exact matches for all 58 published quantitative metrics against the frozen dataset, verifies 16/16 citations, audits UTF-8 encoding fidelity, and proves 0 diffs in `whot_ml/`.

---

## Why These Documents Are Public

These documents are included in the public research artifact to provide end-to-end scientific transparency and auditability:
1. **Pre-Registration:** `P1-D1` documents that experimental setups, sample sizes, and seed schedules were pre-registered before production execution.
2. **Frozen Claims:** `P1-D2` documents that empirical findings and claim boundaries were formally frozen before writing the manuscript, preventing post-hoc hypothesis construction or HARKing (Hypothesizing After Results are Known).
3. **Independent Reproducibility & Auditing:** The two audit documents prove that published tables and figures were independently recomputed from raw Kaggle telemetry and validated against the simulator codebase.
