# P0 Invalid Trial Rate (AC-P0-05-06)

## Scope

- Feature: `F-P0-05-03`
- Story: `S-P0-05-03`
- AC: `AC-P0-05-06`

Requirement under validation:

1. Given invalid trial outcomes, when efficiency metrics are computed, output includes invalid trial rate and reason breakdown.

## Verification Method

Command executed:

```bash
.venv/bin/pytest -q tests/unit/p0_search_efficiency.py
```

## Expected Behavior

1. `invalid_trial_rate` is computed as invalid/total.
2. `invalid_reason_breakdown` supports reason-level drilldown.
3. If all trials invalid, non-computable reason is explicit.

## Evidence

Observed assertions:

1. Normal mixed case: `invalid_trial_rate == 0.2` and reason count includes `nan_prediction=1`.
2. All-invalid case: `invalid_trial_rate == 1.0` and `not_computable_reason == "no_valid_trials"`.

## Result

- Status: `PASS`
- Date: `2026-05-08`
