# P0 Reject Without Evidence (AC-P0-04-02)

## Scope

- Feature: `F-P0-04-01`
- Story: `S-P0-04-02`
- AC: `AC-P0-04-02`

Risk under validation:

1. If a report claim has no evidence links, audit status must be `reject`.

## Verification Method

Command executed:

```bash
.venv/bin/pytest -q tests/unit/p0_claim_evidence_map.py::test_claim_without_evidence_is_rejected
```

## Expected Behavior

1. `dataset_validated_before_execution` -> `reject` when trace evidence is absent.
2. `workflow_execution_completed` -> `reject` when source artifacts are absent.
3. `top_candidates_reported` -> `reject` when ranking source file evidence is absent.

## Evidence

Observed assertions validate all three claims are explicitly marked `reject`.

## Result

- Status: `PASS`
- Date: `2026-05-08`
