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

### Session 3

- Added a workflow result parsing node after successful native workflow execution:
  - parses `gblup/gebv_predictions.csv` for ranked candidate outputs
  - parses `gblup/model_summary.txt` for key model metrics
  - writes structured `workflow_summary` back into job state
- Extended job state schema with:
  - `workflow_summary` (top candidates, total candidates, model metrics, source files)
- Added a report-facing API endpoint: `GET /jobs/{job_id}/report`
  - returns agent-facing explanation text plus top-candidate list
  - enforces `409` for unfinished jobs to keep state semantics explicit
- Updated run execution logic:
  - if workflow output parsing fails, job is marked failed with `workflow_output_parse_error`
- Added tests for:
  - workflow output parsing service
  - report endpoint success and unfinished-job behavior
- Verified full unit suite in `llm_gblup` environment with `25 passed`.

### Session 4

- Implemented delivery-step completion around production-style demo requirements:
  - added `/jobs/{job_id}/artifacts` endpoint for reproducible output manifests
  - added structured execution timeline events in job state (`queued/running/completed/failed`)
  - added error detail surface (`execution_error_detail`) in addition to stable error codes
- Extended workflow output parsing:
  - added optional `accuracy_metrics.rds` extraction via `Rscript + jsonlite` when available
  - merged extracted metrics into `workflow_summary.model_metrics`
- Added native packaging bundle for non-Docker cluster deployment:
  - `packaging/native/environment.yml`
  - `packaging/native/.env.example`
  - `packaging/native/README.md`
  - `scripts/native/preflight.sh`
  - `scripts/native/start_api.sh`
  - `scripts/native/demo_run.sh`
- Added real-data support scripts:
  - `scripts/native/prepare_pig_trait_csv.py`
  - `scripts/native/real_data_contract_check.py`
- Added delivery documentation set:
  - `docs/delivery/REAL_DATA_RUNBOOK.md`
  - `docs/delivery/DEMO_10MIN_SCRIPT.md`
  - `docs/delivery/MVP_ACCEPTANCE_CHECKLIST.md`
- Added a delivery layout smoke test to protect required handoff artifacts.
- Performed one real pig-data contract integration check:
  - converted `data/pig5/BF.txt` to `data/pig5/BF_phenotype.csv`
  - contract check passed against `data/pig5/2548bir.bed` with zero validation flags
- Verified full unit suite in `llm_gblup` environment with `29 passed`.

### Session 5

- Added Slurm-aware execution policy into workflow orchestration:
  - new policy env `ANIMAL_GS_AGENT_WORKFLOW_EXECUTION_POLICY` with `auto|slurm|local`
  - `auto` mode now detects login-node context and routes workflow execution to `sbatch` submission
  - added `ANIMAL_GS_AGENT_SLURM_SUBMIT_SCRIPT` integration for explicit submission scripts
- Extended workflow execution state contract:
  - `WorkflowExecutionResult` now carries `status` (`completed|submitted`) and optional `submission_id`
  - `/jobs/{id}/run` now keeps job in `running` status when Slurm submission is accepted
  - added `workflow_submission_id` field in job response schema
- Updated native packaging docs and env templates with Slurm policy fields.
- Verified full unit suite in `llm_gblup` environment with `32 passed`.

### Session 6

- Added Slurm status polling integration in `GET /jobs/{id}`:
  - if job is `running` with `slurm_nextflow_submit`, API now refreshes state using queue polling
  - auto transitions from running to completed/failed based on Slurm terminal states
  - completed refresh now parses workflow outputs and writes `workflow_summary`
- Added new service module for Slurm state polling:
  - `src/animal_gs_agent/services/slurm_service.py`
  - `sacct` first, `squeue` fallback, normalized states
- Added `workflow_queue_state` to job schemas for explicit queue visibility.
- Added overall roadmap document:
  - `docs/delivery/OVERALL_PLAN.md`
- Verified full unit suite in `llm_gblup` environment with `35 passed`.

### Session 7

- Added practical hardening updates:
  - optional persistent job store via `ANIMAL_GS_AGENT_JOB_STORE_PATH`
  - job state auto-save on lifecycle transitions
  - job reload from disk when in-memory store is empty
  - idempotent `run_job` behavior for `running` and `completed` states
- Added new service tests for practical behavior:
  - persistence/recovery from disk
  - idempotent run execution guard
- Updated overall roadmap progress status in `docs/delivery/OVERALL_PLAN.md`.
- Verified full unit suite in `llm_gblup` environment with `37 passed`.

### Session 8

- Extended practical persistence backend with SQLite option:
  - new env `ANIMAL_GS_AGENT_JOB_STORE_SQLITE_PATH`
  - auto-create and maintain `jobs` table
  - load/recover job states from SQLite when in-memory store is empty
- Kept compatibility with existing JSON-based persistence backend.
- Added practical unit test coverage for SQLite persistence and recovery.
- Updated packaging env template and architecture/roadmap docs to include SQLite mode.
- Verified full unit suite in `llm_gblup` environment with `38 passed`.

### Session 9

- Added practical workerization with async queue mode:
  - new SQLite-backed run queue service (`run_queue_service.py`)
  - enqueue endpoint behavior gated by `ANIMAL_GS_AGENT_ASYNC_RUN_ENABLED=1`
  - `POST /jobs/{id}/run` can now enqueue instead of immediate execution
  - added worker consumer entrypoint `scripts/native/worker_loop.py`
- Added unit test coverage for:
  - queue enqueue/claim semantics
  - async run API behavior
- Updated delivery layout smoke test and native packaging docs for worker script.
- Updated full-picture and overall-plan docs with async mode architecture.
- Verified full unit suite in `llm_gblup` environment with `41 passed`.

### Session 10

- Added worker control-plane service and API routes:
  - `GET /worker/health`
  - `POST /worker/process-once`
- Added worker service layer for queue snapshot and one-shot queue consumption.
- Added unit tests for:
  - worker service behavior (`test_worker_service.py`)
  - worker API routes (`test_worker_routes.py`)
- Updated README/native packaging/overall plan docs to include worker control-plane endpoints.
- Verified full unit suite in `llm_gblup` environment with `45 passed`.
