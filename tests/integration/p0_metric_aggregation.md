# P0 Metric Aggregation (AC-P0-05-02)

## Scope

- Feature: `F-P0-05-01`
- Story: `S-P0-05-01`
- AC: `AC-P0-05-02`

Requirement under validation:

1. Given multiple trials, when aggregation runs, grouped statistics by population/trait/model are produced.

## Verification Method

Command executed:

```bash
.venv/bin/pytest -q tests/unit/p0_metric_pearson_rmse.py::test_aggregate_trial_metrics_by_population_trait_model
```

## Expected Behavior

1. Aggregation groups by `(population, trait, model_id)`.
2. Output includes `trial_count`, `mean_pearson`, `mean_rmse`.

## Evidence

Observed assertions:

1. Two groups are returned from mixed trial records.
2. `("pig5", "daily_gain", "GBLUP")` group has `trial_count == 2`.
3. Group-level mean metrics are available and valid.

## Result

- Status: `PASS`
- Date: `2026-05-08`
