# P0 Metric Consistency Check (AC-P0-04-04)

## Scope

- Feature: `F-P0-04-02`
- Story: `S-P0-04-03`
- AC: `AC-P0-04-04`

Requirement under validation:

1. Given reported metrics, when value ranges are inconsistent, audit output must raise metric consistency risk.

## Verification Method

Command executed:

```bash
.venv/bin/pytest -q tests/unit/p0_claim_evidence_map.py::test_audit_checks_detect_leakage_and_metric_conflict
```

## Expected Behavior

1. `run_audit_checks(...)` returns `metric_consistency_check`.
2. `metric_consistency_check.status == "risk"` for out-of-range metric values.

## Evidence

Observed assertion:

1. `by_check["metric_consistency_check"].status == "risk"`

## Result

- Status: `PASS`
- Date: `2026-05-08`
