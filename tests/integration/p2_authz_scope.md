# P2 AuthZ Scope Integration Evidence

## Scope

- Req: `F-P2-03-01`
- AC: `AC-P2-03-01`
- Goal: verify submission is denied when request scope is outside caller authorization scope.

## Command

```bash
pytest -q tests/unit/api/test_governance_controls.py::test_submit_job_rejects_when_scope_not_authorized
```

## Result

- PASS (`1 passed`)
- Job submission with `project_scope=project_a` and `access_scopes=[project_b]` is blocked.
- API returns `403` (`authz_scope_denied`).
