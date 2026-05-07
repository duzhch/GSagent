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
- Integrated task-understanding results into `/jobs` submission and job status records.
- The job API now stores and returns structured task-understanding output together with the job metadata.
- Added a first dataset profiling layer to job submission, currently focused on path-level existence checks for genotype and phenotype inputs.
- Changed the initial job lifecycle state from `pending` to `queued` to better reflect pre-execution workflow staging.

## 2026-05-07

### Session 1

- Expanded dataset profiling from simple path checks to lightweight dataset introspection:
  - file format inference for phenotype/genotype inputs
  - phenotype header extraction for CSV/TSV/TXT sources
  - trait-column presence checks tied to the submitted `trait_name`
  - explicit `validation_flags` for missing files, unsupported formats, and missing trait columns
- Added a first explicit job execution endpoint: `POST /jobs/{job_id}/run`.
- Implemented in-memory job state transitions:
  - `queued -> running -> completed` when validation passes
  - `queued -> running -> failed` when validation flags are present
- Added failure surfacing through `execution_error` in job status records.
- Added new unit tests for:
  - dataset profile header/trait detection
  - run endpoint transitions for valid and invalid datasets
- Verified full unit suite in `llm_gblup` environment with `18 passed`.

### Session 2

- Added a fixed workflow execution service to bridge agent decisions with a real GS pipeline backend:
  - introduced `workflow_service` with a native Nextflow executor
  - fixed command assembly for `main.nf` with explicit trait/genotype/phenotype/outdir parameters
  - standardized workflow errors as typed codes (`workflow_pipeline_missing`, `workflow_input_invalid`, `workflow_runtime_error`)
- Upgraded `/jobs/{job_id}/run` from validation-only completion to true execution dispatch:
  - route now calls the fixed workflow executor
  - `run_job` now supports executor injection and workflow error mapping
  - successful runs now persist workflow metadata (`workflow_backend`, `workflow_result_dir`)
- Expanded genotype format support in dataset profiling to include `vcf` so native Nextflow input contracts are accepted.
- Added and updated tests:
  - API run tests now validate workflow success and workflow-runtime failure branches
  - new workflow service tests cover command construction and missing-pipeline failures
- Verified full unit suite in `llm_gblup` environment with `21 passed`.
