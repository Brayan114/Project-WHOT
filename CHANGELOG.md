# Changelog

## v1.0.1 — Bug Fix Release

- **Fixed:** `StackingMode.NO_STACKING` was ignored by the penalty-defense legality check in `whot_ml/rules_engine.py`. Setting `NO_STACKING` for Pick Two or Pick Three would silently fall back to `SAME_EFFECT` behavior. Fixed in commit `<COMMIT_HASH>`.
- **Added:** Regression tests `test_no_stacking_*` covering all three stacking modes.
- **Unchanged:** Baseline `WHOT-NG-v1` behavior (which uses `SAME_EFFECT`). Existing 109 tests continue to pass unmodified.

## v1.0.0 — Initial Release

- Frozen simulator at commit `7c1a2dc`.
- 109 passing tests.
- Paper 1 experimental apparatus.
