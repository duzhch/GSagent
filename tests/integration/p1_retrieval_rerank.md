# P1 Retrieval Re-rank Integration Evidence

## Scope

- Req: `F-P1-01-02`
- AC: `AC-P1-01-02`
- Goal: verify retrieval can rank higher-relevance evidence above low-relevance evidence.

## Command

```bash
pytest -q tests/unit/p1_knowledge_rag.py::test_retrieval_rerank_prefers_more_relevant_documents
```

## Result

- PASS (`1 passed`)
- Query: `batch covariate strategy`.
- Ranked result puts SOP document (`sop-1`) above unrelated literature text.
- Score ordering is monotonic (`rank[0] >= rank[1]`), confirming deterministic rerank behavior.
