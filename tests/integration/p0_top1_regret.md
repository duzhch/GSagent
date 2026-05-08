# P0 Top-1 And Regret (AC-P0-05-03)

## Scope

- Feature: `F-P0-05-02`
- Story: `S-P0-05-02`
- AC: `AC-P0-05-03`

Requirement under validation:

1. Given task decision output, when decision quality metrics run, system returns Top-1 hit and Regret.

## Verification Method

Command executed:

```bash
.venv/bin/pytest -q tests/unit/p0_top1_regret.py::test_decision_quality_outputs_top1_and_regret
```

## Expected Behavior

1. Top-1 hit is true when selected model matches best candidate score.
2. Regret is computed against oracle best score.

## Evidence

Observed assertions:

1. `top1_hit == True`
2. `regret == 0.0`
3. `not_computable_reason is None`

## Result

- Status: `PASS`
- Date: `2026-05-08`
