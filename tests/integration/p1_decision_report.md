# P1 Decision Report Template Evidence

## Scope

- Req: `F-P1-03-02`
- AC: `AC-P1-03-02`
- Goal: verify decision role report exists and aligns with technical/management conclusions.

## Command

```bash
pytest -q tests/unit/api/test_job_report.py::test_job_report_includes_role_specific_reports_with_consistent_conclusion
```

## Result

- PASS (`1 passed`)
- `role_reports` includes `decision` role.
- Role conclusion alignment check:
  - `role_report_alignment_ok=true`
  - all role conclusions are identical.
