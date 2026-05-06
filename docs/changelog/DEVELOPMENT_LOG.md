# Development Log

## 2026-05-06

### Session 1

- Created the standalone `animal_gs_agent` git repository to avoid mixing the new animal-breeding architecture with the older `gs_prototype` scaffold.
- Wrote the first architecture spec for the LangGraph-based MVP.
- Wrote the initial implementation plan with TDD-oriented tasks.
- Established repository maintenance rules:
  - use git commits for each meaningful change
  - keep a human-readable development log
  - record major architecture decisions as ADRs
- Configured the repository to use the `llm_gblup` conda environment for development.
- Added the first FastAPI service skeleton and verified the `/health` endpoint with a passing unit test.
- Installed the initial Python dependencies into the `llm_gblup` conda environment.
- Added the first agent intake contract for supported genomic selection requests and verified it with a passing unit test.
- Added a standalone development strategy document to preserve the current and future engineering direction.
- Added the first `/jobs` submission contract with typed request and response schemas.
- Verified that the current unit test set passes in the `llm_gblup` environment.
