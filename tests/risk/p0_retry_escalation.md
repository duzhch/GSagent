# TC-P0-01-02 Retry Escalation Risk Evidence

- Req ID: `F-P0-01-01`
- AC ID: `AC-P0-01-02`
- Test Case ID: `TC-P0-01-02`
- Date: `2026-05-08`

## Scope

Validate that worker failure handling does not perform unlimited blind retries:

1. Failure under retry budget is requeued.
2. Failure when retry budget is exhausted transitions to `dead`.
3. `dead` queue records are marked as escalated for manual intervention.
4. Job status is marked `escalation_required=true` with escalation reason and decision-trace node `escalate_human_review`.

## Automated Evidence

- `tests/unit/services/test_run_queue_service.py::test_failed_attempt_under_budget_is_requeued`
- `tests/unit/services/test_run_queue_service.py::test_failed_attempt_over_budget_becomes_dead_and_escalated`
- `tests/unit/services/test_worker_service.py::test_process_next_queued_job_escalates_after_retry_budget`

Command:

```bash
python -m pytest tests/unit/services/test_run_queue_service.py tests/unit/services/test_worker_service.py -q
```

Observed result:

- `7 passed`

## Result

- Dev evidence status: `PASS`
- QA integrated replay: pending
