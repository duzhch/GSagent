# P2 Observability Audit E2E Evidence

## Scope

- Req: `F-P2-03-03`
- AC: `AC-P2-03-03`
- Goal: verify governance audit endpoint exposes observability counters and execution status.

## Command

```bash
pytest -q tests/unit/api/test_governance_controls.py::test_governance_audit_endpoint_returns_observability_snapshot
```

## Result

- PASS (`1 passed`)
- Endpoint `GET /jobs/{job_id}/governance/audit` returns:
  - `event_count`
  - `decision_count`
  - `execution_status`
  - `project_scope`
  - `requested_by`
