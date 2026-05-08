# P1 Knowledge Connector Integration Evidence

## Scope

- Req: `F-P1-01-01`
- AC: `AC-P1-01-01`
- Goal: verify report suggestions can attach at least one knowledge evidence item from configured sources.

## Command

```bash
pytest -q tests/unit/api/test_job_report.py::test_job_report_includes_knowledge_citations
```

## Result

- PASS (`1 passed`)
- Report response includes `knowledge_citations`.
- First citation contains recommendation text with `covariate=batch` and non-empty evidence list.
- Evidence sources include configured SOP/literature files plus historical task summaries.
