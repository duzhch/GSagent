# TC-P0-01-03 Trace Visibility E2E Evidence

- Req ID: `F-P0-01-01`
- AC ID: `AC-P0-01-03`
- Test Case ID: `TC-P0-01-03`
- Date: `2026-05-08`

## Scope

Validate trace visibility on job detail and trace endpoint:

1. `GET /jobs/{job_id}` includes node input/output/status.
2. `GET /jobs/{job_id}/trace` exposes structured node list with status and duration.
3. Job detail includes escalation visibility fields (`escalation_required`, `escalation_reason`, `escalation_requested_at`).

## Automated Evidence

- `tests/unit/api/test_job_status.py::test_get_job_returns_submitted_job_status`
- `tests/unit/api/test_job_trace.py::test_get_job_trace_returns_decision_nodes`
- `tests/unit/p0_trace_schema_test.py::test_decision_trace_is_initialized_with_required_fields`

Command:

```bash
python -m pytest tests/unit/p0_trace_schema_test.py tests/unit/api/test_job_status.py tests/unit/api/test_job_trace.py -q
```

Observed result:

- Passing in current branch; trace nodes include `input_summary`, `output_summary`, `status`, `duration_ms`.

## Result

- Dev evidence status: `PASS`
- QA e2e replay: pending
