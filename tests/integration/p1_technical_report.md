# P1 Technical Report Template Evidence

## Scope

- Req: `F-P1-03-01`
- AC: `AC-P1-03-01`
- Goal: verify technical role report exists and shares a consistent conclusion with other roles.

## Command

```bash
pytest -q tests/unit/api/test_job_report.py::test_job_report_includes_role_specific_reports_with_consistent_conclusion
```

## Result

- PASS (`1 passed`)
- `role_reports` includes `technical` role.
- `technical` report includes:
  - shared conclusion
  - audit summary
  - risk summary
