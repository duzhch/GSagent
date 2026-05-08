# P0 Oracle Missing Handling (AC-P0-05-04)

## Scope

- Feature: `F-P0-05-02`
- Story: `S-P0-05-02`
- AC: `AC-P0-05-04`

Risk under validation:

1. If oracle-best reference is missing, system must return an explicit non-computable reason.

## Verification Method

Command executed:

```bash
.venv/bin/pytest -q tests/unit/p0_top1_regret.py::test_decision_quality_returns_reason_when_oracle_missing
```

## Expected Behavior

1. `regret` is `None` when oracle best score is unavailable.
2. `not_computable_reason` is set to an explicit value.

## Evidence

Observed assertions:

1. `regret is None`
2. `not_computable_reason == "oracle_best_missing"`

## Result

- Status: `PASS`
- Date: `2026-05-08`
