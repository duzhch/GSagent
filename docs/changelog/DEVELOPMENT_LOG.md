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
- Added a minimal in-memory job registry so submitted jobs can be queried by `job_id`.
- Verified the current four-test unit suite after adding job status lookup.
- Added repository-local skills and reference documents for the animal GS baseline and the OpenAI-compatible model gateway.
- Added the first model-layer schema, OpenAI-compatible client primitives, and task-understanding pipeline with fallback parsing.
- Verified the current nine-test unit suite after the model integration groundwork.
- Added environment-variable based model configuration for OpenAI-compatible providers.
- Added a first `POST /agent/parse-task` route so task understanding can be exercised through the API before real provider credentials are wired in.
- Verified the current eleven-test unit suite after exposing the parsing route.
- Removed fallback behavior for task understanding; the agent now returns explicit API errors when the provider is missing, fails, or returns invalid structured output.
- Verified the current thirteen-test unit suite after switching task understanding to provider-required behavior.
- Tightened the OpenAI-compatible payload to request JSON-mode responses.
- Added payload normalization for near-miss provider field names so real DeepSeek responses can be mapped into the repository schema.
- Verified a real DeepSeek smoke test for task parsing with the current `OpenAICompatibleLLMClient` path.
- Verified the current fourteen-test unit suite after the real-provider compatibility changes.
