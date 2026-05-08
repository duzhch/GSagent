# P1 Preventive Actions E2E Evidence

## Scope

- Req: `F-P1-02-03`
- AC: `AC-P1-02-03`
- Goal: verify high-similarity badcase hit produces explicit preventive actions.

## Command

```bash
pytest -q tests/unit/p1_badcase_schema.py::test_badcase_similarity_returns_preventive_actions_when_high_similarity
```

## Result

- PASS (`1 passed`)
- For a highly similar historical case, advice output includes:
  - `high_similarity_hit=true`
  - non-empty `preventive_actions`
- Returned actions include historical recommendation reuse (`covariate=batch`) instead of silent execution.
