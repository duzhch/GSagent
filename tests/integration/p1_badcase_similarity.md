# P1 Badcase Similarity Integration Evidence

## Scope

- Req: `F-P1-02-02`
- AC: `AC-P1-02-02`
- Goal: verify new tasks query historical badcases and detect high-similarity cases.

## Command

```bash
pytest -q tests/unit/services/test_job_service_practical.py::test_create_job_queries_historical_badcase_and_emits_preventive_actions
```

## Result

- PASS (`1 passed`)
- New job creation executes badcase query before run.
- Similarity hit is marked as `high_similarity_hit=true`.
- At least one similar historical case is returned in `badcase_advice.similar_cases`.
