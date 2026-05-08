# P0 Structure Risk Tag Evidence

## Scope

- Req ID: `F-P0-02-02`
- AC ID: `AC-P0-02-05`
- Test Case ID: `TC-P0-02-05`

## Intent

Verify significant population-structure risk is carried forward as model-stage risk tags.

## Command

```bash
cd /work/home/zyqlab/dzhichao/Agent0428/animal_gs_agent
.venv/bin/python -m pytest tests/unit/api/test_job_run.py::test_run_job_carries_population_risk_tags_into_execution_stage -q
```

## Result

- Exit code: `0`
- Status: `PASS`
- Assertion highlights:
  - run response remains executable (not hard blocked by structure-only risk)
  - `dataset_profile.risk_tags` contains `population_structure_outliers`
