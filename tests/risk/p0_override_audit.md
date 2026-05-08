# P0 QC Override Audit Evidence

## Scope

- Req ID: `F-P0-02-01`
- AC ID: `AC-P0-02-03`
- Test Case ID: `TC-P0-02-03`

## Intent

Verify manual override on a QC-blocked job records approver and reason, then re-queues the job.

## Command

```bash
cd /work/home/zyqlab/dzhichao/Agent0428/animal_gs_agent
.venv/bin/python -m pytest tests/unit/api/test_job_qc_override.py::test_qc_override_requeues_blocked_job -q
```

## Result

- Exit code: `0`
- Status: `PASS`
- Assertion highlights:
  - `POST /jobs/{job_id}/qc/override` returns `200`
  - `qc_override_applied=true`
  - `qc_override_by=<approver>`
  - decision trace includes `approve_qc_override`
