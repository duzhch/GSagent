# P0 Trials-to-95%-Best (AC-P0-05-05)

## Scope

- Feature: `F-P0-05-03`
- Story: `S-P0-05-03`
- AC: `AC-P0-05-05`

Requirement under validation:

1. Given search trial records, when efficiency metrics are computed, output includes trials needed to reach 95% of best score.

## Verification Method

Command executed:

```bash
.venv/bin/pytest -q tests/unit/p0_search_efficiency.py::test_search_efficiency_outputs_trials_to_95_and_invalid_rate
```

## Expected Behavior

1. `trials_to_95_best` is returned as first trial index reaching threshold score.

## Evidence

Observed assertion:

1. `trials_to_95_best == 4`

## Result

- Status: `PASS`
- Date: `2026-05-08`
