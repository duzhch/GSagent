# P0 Cross-Pop Validation Protocol (AC-P0-03-07)

## Scope

- Feature: `F-P0-03-03`
- Story: `S-P0-03-04`
- AC: `AC-P0-03-07`

Requirement under validation:

1. Given a cross-pop task, when evaluation planning is generated, the system outputs cross-pop protocol and generalization metrics.

## Verification Method

Command executed:

```bash
.venv/bin/pytest -q tests/unit/services/test_job_service_practical.py::test_create_job_attaches_validation_protocol_plan
```

## Expected Behavior

1. Job creation result contains `validation_protocol_plan`.
2. `cross_pop` protocol exists.
3. Cross-pop metric set is present.
4. Split record explicitly marks held-out validation population.

## Evidence

Observed assertions:

1. `scenario_id=cross_pop` exists.
2. Metrics include `cross_pop_pearson` and `cross_pop_rmse`.
3. Primary split uses `train_population="pig"` and `validation_population="held-out population"`.

## Result

- Status: `PASS`
- Date: `2026-05-08`
