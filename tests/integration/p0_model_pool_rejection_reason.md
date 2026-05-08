# P0 Model Pool Rejection Reason (AC-P0-03-02)

## Scope

- Feature: `F-P0-03-01`
- Story: `S-P0-03-01`
- AC: `AC-P0-03-02`

Requirement under validation:

1. Given data does not satisfy model requirements, when execution planning is built, the system must mark unavailable reasons.

## Verification Method

Command executed:

```bash
.venv/bin/pytest -q tests/unit/api/test_job_submission.py::test_submit_job_includes_model_pool_disable_reasons
```

## Expected Behavior

1. `POST /jobs` response contains `model_pool_plan`.
2. Candidate entries include `available=false` and explicit `disabled_reasons` when constraints are unmet.

## Evidence

Observed assertions from automated test:

1. `GBLUP` is unavailable with reason `trait_column_missing`.
2. `BayesB` is unavailable with reason `insufficient_trait_records_for_bayesb`.
3. `XGBoost` is unavailable with reason `qc_risk_high`.

## Result

- Status: `PASS`
- Date: `2026-05-08`
