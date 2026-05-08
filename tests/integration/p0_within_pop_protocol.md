# P0 Within-Pop Validation Protocol (AC-P0-03-06)

## Scope

- Feature: `F-P0-03-03`
- Story: `S-P0-03-04`
- AC: `AC-P0-03-06`

Requirement under validation:

1. Given a within-pop task, when evaluation planning is generated, the system outputs within-pop protocol and metrics.

## Verification Method

Command executed:

```bash
.venv/bin/pytest -q tests/unit/services/test_job_service_practical.py::test_create_job_attaches_validation_protocol_plan
```

## Expected Behavior

1. Job creation result contains `validation_protocol_plan`.
2. `within_pop` protocol exists.
3. `within_pop` metric set is present.
4. Split record keeps train/validation in same population.

## Evidence

Observed assertions:

1. `scenario_id=within_pop` exists.
2. Metrics include `within_pop_pearson` and `within_pop_rmse`.
3. `train_population == validation_population == "pig"` for primary split.

## Result

- Status: `PASS`
- Date: `2026-05-08`
