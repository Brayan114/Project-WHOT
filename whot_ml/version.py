"""Version metadata for WHOT-ML simulator and baseline environment."""

# v1.0.1 fixes a defect where StackingMode.NO_STACKING was ignored in rules_engine.py
# and silently defaulted to SAME_EFFECT. Baseline WHOT-NG-v1.0 (SAME_EFFECT) remains unchanged.
SIMULATOR_VERSION = "1.0.1"
BASELINE_ENVIRONMENT = "WHOT-NG-v1.0"
SPECIFICATION_VERSION = "Phase 0 (P0-D1 to P0-D5 v0.1)"
FROZEN_BASELINE = True
