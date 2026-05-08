# TC-P0-01-01 Supervisor Flow Integration Evidence

- Req ID: `F-P0-01-01`
- AC ID: `AC-P0-01-01`
- Test Case ID: `TC-P0-01-01`
- Date: `2026-05-08`

## Scope

Validate that a valid job request executes governance path and outputs complete decision trace.

Expected path:

1. intake accept (`accept_job`)
2. execution start (`start_workflow`)
3. completion verdict (`finalize_completed`) or failure verdict

## Automated Evidence

- `tests/unit/api/test_job_run.py::test_run_job_transitions_to_completed_for_valid_dataset`
- `tests/unit/api/test_job_status.py::test_get_job_returns_submitted_job_status`

Command:

```bash
python -m pytest tests/unit/api/test_job_run.py tests/unit/api/test_job_status.py -q
```

Observed result:

- Passing in current branch with expected decision trace assertions.

## Result

- Dev evidence status: `PASS`
- QA replay: pending
