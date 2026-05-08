# P1 Evidence Conflict Risk Test

## Scope

- Req: `F-P1-01-03`
- AC: `AC-P1-01-03`
- Goal: verify conflicting evidence is explicitly marked and missing evidence is rejected.

## Command

```bash
pytest -q tests/unit/p1_knowledge_rag.py::test_citation_conflict_is_marked_and_missing_evidence_is_rejected
```

## Result

- PASS (`1 passed`)
- Positive and negative guidance on the same recommendation triggers:
  - `conflict=true`
  - `conflict_note=evidence_conflict_detected: ...`
- Empty knowledge corpus for a required recommendation raises `ValueError`, preventing silent evidence omission.
