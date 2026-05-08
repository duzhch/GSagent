# P2 Retry Policy Integration Evidence

## Scope

- Req: `F-P2-02-02`
- AC: `AC-P2-02-02`
- Goal: verify debug diagnosis emits retry/escalation recommendation with bounded retry policy.

## Command

```bash
pytest -q tests/unit/p2_failure_classifier.py::test_debug_retry_policy_recommends_action_and_retry_budget
```

## Result

- PASS (`1 passed`)
- `workflow_runtime_error` is classified as `code`.
- Diagnosis outputs:
  - `retryable=true`
  - `suggested_retry_decision=retry`
  - non-empty remediation action
  - explicit attempt/max_attempts context.
