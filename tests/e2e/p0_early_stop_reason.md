# P0 Early Stop Reason (AC-P0-03-04)

## Scope

- Feature: `F-P0-03-02`
- Story: `S-P0-03-02`
- AC: `AC-P0-03-04`

Requirement under validation:

1. Given early-stop condition is triggered, when strategy search stops, the system must output stop reason and current best plan.

## Verification Method

Command executed:

```bash
.venv/bin/pytest -q tests/unit/api/test_job_submission.py::test_submit_job_includes_trial_stop_reason
```

## Expected Behavior

1. `POST /jobs` response includes `trial_strategy_plan`.
2. `trial_strategy_plan.stop_reason` is explicitly set when early-stop triggers.
3. `budget_consumed` is less than configured `max_trials`.

## Evidence

Observed assertions:

1. `trial_strategy_plan.stop_reason == "early_stop_no_improvement"`.
2. `trial_strategy_plan.budget_consumed < 10`.

## Result

- Status: `PASS`
- Date: `2026-05-08`
