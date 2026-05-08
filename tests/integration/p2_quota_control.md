# P2 Quota Control Integration Evidence

## Scope

- Req: `F-P2-03-02`
- AC: `AC-P2-03-02`
- Goal: verify project-level active job quota blocks additional submissions.

## Command

```bash
pytest -q tests/unit/api/test_governance_controls.py::test_submit_job_rejects_when_project_quota_exceeded
```

## Result

- PASS (`1 passed`)
- With `ANIMAL_GS_AGENT_PROJECT_QUOTA_MAX_ACTIVE=1`:
  - first submission is accepted
  - second submission in same scope is rejected with `429` (`project_quota_exceeded`)
