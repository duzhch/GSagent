# P0 QC Blocking Evidence

## Scope

- Req ID: `F-P0-02-01`
- AC ID: `AC-P0-02-02`
- Test Case ID: `TC-P0-02-02`

## Intent

Verify that high QC risk blocks workflow execution by default.

## Command

```bash
cd /work/home/zyqlab/dzhichao/Agent0428/animal_gs_agent
.venv/bin/python -m pytest tests/unit/api/test_job_run.py::test_run_job_blocks_before_workflow_when_qc_risk_is_high -q
```

## Result

- Exit code: `0`
- Status: `PASS`
- Assertion highlights:
  - job status becomes `failed`
  - `execution_error=qc_risk_high_blocked`
  - workflow executor is not entered
