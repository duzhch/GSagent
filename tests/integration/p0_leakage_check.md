# P0 Leakage Check (AC-P0-04-03)

## Scope

- Feature: `F-P0-04-02`
- Story: `S-P0-04-03`
- AC: `AC-P0-04-03`

Requirement under validation:

1. Given train/validation split audit context, when leakage evidence is found, audit output must mark leakage risk.

## Verification Method

Command executed:

```bash
.venv/bin/pytest -q tests/unit/p0_claim_evidence_map.py::test_audit_checks_detect_leakage_and_metric_conflict
```

## Expected Behavior

1. `run_audit_checks(...)` returns `leakage_check`.
2. `leakage_check.status == "risk"` when leakage overlap evidence exists.

## Evidence

Observed assertion:

1. `by_check["leakage_check"].status == "risk"`

## Result

- Status: `PASS`
- Date: `2026-05-08`
