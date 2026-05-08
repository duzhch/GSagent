# P1 Management Report Template Evidence

## Scope

- Req: `F-P1-03-03`
- AC: `AC-P1-03-03`
- Goal: verify management role report exists and includes audit/risk summaries.

## Command

```bash
pytest -q tests/unit/api/test_job_report.py::test_job_report_includes_role_specific_reports_with_consistent_conclusion
```

## Result

- PASS (`1 passed`)
- `role_reports` includes `management` role.
- Management report includes:
  - audit summary
  - risk summary
  - shared conclusion consistent with technical and decision reports
