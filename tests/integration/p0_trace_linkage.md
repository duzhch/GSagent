# TC-P0-01-05 Trace Linkage Evidence

- Req ID: `F-P0-01-02`
- AC ID: `AC-P0-01-05`
- Test Case ID: `TC-P0-01-05`
- Date: `2026-05-08`

## Scope

Verify that decision-trace records are queryable from API and each key conclusion can be traced to source node fields (`decision_id`, `agent_id`, `action`, `evidence`).

## Automated Evidence

- `tests/unit/api/test_job_trace.py::test_get_job_trace_returns_decision_nodes`
- `tests/unit/p0_trace_schema_test.py::test_decision_trace_is_initialized_with_required_fields`

Run command:

```bash
python -m pytest tests/unit/p0_trace_schema_test.py tests/unit/api/test_job_trace.py -q
```

Observed result:

- `3 passed`

## Result

- Current dev status: `PASS` (developer-side evidence ready)
- QA status: pending independent integration replay
