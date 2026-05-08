# TC-P1-04-01 Approval Gate Risk Evidence

- Req ID: `F-P1-04-01`
- AC ID: `AC-P1-04-01`
- Test Case ID: `TC-P1-04-01`
- Date: `2026-05-08`

## Scope

Validate high-risk escalation handling requires explicit human approval and cannot silently bypass gate.

Checks:

1. Escalated job can be retried only through approval endpoint.
2. Non-escalated job calling approval retry endpoint returns `409`.
3. Approval action requires accountable payload (`approver`, `reason`).

## Automated Evidence

- `tests/unit/api/test_job_escalation.py::test_retry_escalated_job_requires_reason_and_requeues`
- `tests/unit/api/test_job_escalation.py::test_retry_non_escalated_job_returns_409`

Command:

```bash
python -m pytest tests/unit/api/test_job_escalation.py -q
```

Observed result:

- `3 passed`

## Result

- Dev evidence status: `PASS`
- QA risk replay: pending
