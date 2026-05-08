# P1 Abort And Fallback E2E Evidence

## Scope

- Req: `F-P1-04-03`
- AC: `AC-P1-04-03`
- Goal: verify forced abort emits explicit fallback plan for controlled rollback.

## Command

```bash
pytest -q tests/unit/api/test_job_escalation.py::test_abort_escalated_job_records_manual_abort
```

## Result

- PASS (`1 passed`)
- Escalated abort keeps full audit trail and sets:
  - `execution_error=manual_abort_after_escalation`
  - `fallback_plan.strategy=manual_review_with_fixed_pipeline_fallback`
  - `fallback_plan.reason`
  - `fallback_plan.created_by`
