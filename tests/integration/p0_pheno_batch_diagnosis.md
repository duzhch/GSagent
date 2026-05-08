# P0 Phenotype Batch Diagnosis Evidence

## Scope

- Req ID: `F-P0-02-03`
- AC ID: `AC-P0-02-06`
- Test Case ID: `TC-P0-02-06`

## Intent

Verify phenotype diagnostics include outlier ratio and batch-effect significance outputs.

## Command

```bash
cd /work/home/zyqlab/dzhichao/Agent0428/animal_gs_agent
.venv/bin/python -m pytest tests/unit/services/test_dataset_profile_service.py::test_build_dataset_profile_generates_phenotype_outlier_and_batch_diagnostics -q
```

## Result

- Exit code: `0`
- Status: `PASS`
- Assertion highlights:
  - `phenotype_diagnostics.outlier_ratio` is populated
  - `phenotype_diagnostics.batch_effect_significant=true` when effect size threshold is exceeded
