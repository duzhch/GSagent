# P0 Population Structure Evidence

## Scope

- Req ID: `F-P0-02-02`
- AC ID: `AC-P0-02-04`
- Test Case ID: `TC-P0-02-04`

## Intent

Verify the agent can parse population structure diagnostics and produce PCA/outlier artifacts in profile state.

## Command

```bash
cd /work/home/zyqlab/dzhichao/Agent0428/animal_gs_agent
.venv/bin/python -m pytest tests/unit/services/test_dataset_profile_service.py::test_build_dataset_profile_parses_population_structure_and_outliers -q
```

## Result

- Exit code: `0`
- Status: `PASS`
- Assertion highlights:
  - `population_structure.sample_count` is populated
  - `outlier_samples` contains expected sample IDs
  - `high_relatedness_pair_count` is populated from relatedness input
