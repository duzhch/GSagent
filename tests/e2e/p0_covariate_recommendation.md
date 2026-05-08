# P0 Covariate Recommendation Evidence

## Scope

- Req ID: `F-P0-02-03`
- AC ID: `AC-P0-02-07`
- Test Case ID: `TC-P0-02-07`

## Intent

Verify significant batch effect triggers model-stage recommendation text for covariate or stratification strategy.

## Command

```bash
cd /work/home/zyqlab/dzhichao/Agent0428/animal_gs_agent
.venv/bin/python -m pytest tests/unit/api/test_job_report.py::test_job_report_includes_covariate_recommendation_when_batch_effect_significant -q
```

## Result

- Exit code: `0`
- Status: `PASS`
- Assertion highlights:
  - report text includes `covariate=batch` recommendation
  - recommendation survives full submit->run->report chain
