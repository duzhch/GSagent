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

### Session 11

- Implemented P0 decision-trace standardization slice (`F-P0-01-02`):
  - added typed `DecisionTraceNode` and `JobDecisionTraceResponse` schemas
  - added `decision_trace` persistence field to job submission/status contracts
  - added `GET /jobs/{job_id}/trace` API for trace replay
  - appended decision nodes across key job lifecycle transitions (accept/run/block/fail/complete/slurm refresh)
- Aligned runtime behavior with strict model requirement:
  - removed `/jobs` fallback heuristic parsing when LLM is not configured
  - `/jobs` now returns `503` with explicit provider-not-configured error
- Added tests and evidence:
  - `tests/unit/p0_trace_schema_test.py`
  - `tests/unit/api/test_job_trace.py`
  - updated `tests/unit/api/test_job_submission.py` for strict no-fallback behavior
  - added integration evidence doc `tests/integration/p0_trace_linkage.md`
- Updated acceptance matrix status:
  - `AC-P0-01-04` -> `PASS`
  - `AC-P0-01-05` -> `IN_PROGRESS`
- Verified full unit suite in `llm_gblup` environment with `53 passed`.

### Session 12

- Implemented retry-budget escalation hardening for `F-P0-01-01 / AC-P0-01-02`:
  - upgraded `run_queue` schema with governance fields:
    - `max_attempts`
    - `next_retry_at`
    - `escalated`
    - `escalation_reason`
  - added bounded retry decision path:
    - failure under budget requeues to `pending` with delayed retry
    - failure over budget transitions to `dead` with escalation mark
- Extended worker behavior to stop blind retries:
  - worker failure now calls queue retry decision and returns structured escalation status
  - worker health now reports both `pending_jobs` and `dead_jobs`
- Added queue observability endpoint:
  - `GET /worker/queue/{job_id}` for queue-state replay and audit
- Added and updated tests:
  - `tests/unit/services/test_run_queue_service.py`
  - `tests/unit/services/test_worker_service.py`
  - `tests/unit/api/test_worker_routes.py`
- Added risk-evidence note:
  - `tests/risk/p0_retry_escalation.md`
- Updated trace matrix:
  - `AC-P0-01-02` -> `IN_PROGRESS` with linked evidence file
- Verified full unit suite in `llm_gblup` environment with `57 passed`.

### Session 13

- Continued P0 bundled-acceptance preparation across multiple ACs:
  - `AC-P0-01-01` supervisor flow evidence
  - `AC-P0-01-03` trace visibility evidence
  - `AC-P0-01-05` trace linkage closure
- Strengthened decision-trace schema for visibility requirements:
  - added node-level `status` and `duration_ms` fields
  - propagated those fields through `/jobs/{id}` and `/jobs/{id}/trace` responses
- Added and updated automated checks:
  - updated `tests/unit/p0_trace_schema_test.py`
  - updated `tests/unit/api/test_job_trace.py`
  - updated `tests/unit/api/test_job_status.py`
  - updated `tests/unit/api/test_job_run.py`
- Added acceptance evidence files:
  - `tests/integration/p0_supervisor_flow.md`
  - `tests/e2e/p0_trace_visibility.md`
- Updated trace matrix status:
  - `AC-P0-01-01` -> `IN_PROGRESS`
  - `AC-P0-01-03` -> `IN_PROGRESS`
  - `AC-P0-01-05` -> `PASS`
- Verified full unit suite in `llm_gblup` environment with `58 passed`.

### Session 14

- Completed practical escalation visibility improvements for unified P0 acceptance:
  - added job-level escalation fields:
    - `escalation_required`
    - `escalation_reason`
    - `escalation_requested_at`
  - worker dead-letter escalation now updates job status and appends decision-trace node:
    - action: `escalate_human_review`
    - story mapping: `S-P0-01-02`
- Added decision-trace artifact persistence:
  - `decision_trace.json` now written alongside workflow outputs (or trace output root fallback)
  - `/jobs/{id}/artifacts` now includes this trace artifact for completed jobs
- Updated tests:
  - `tests/unit/services/test_worker_service.py`
  - `tests/unit/api/test_job_status.py`
  - `tests/unit/api/test_job_artifacts.py`
- Updated acceptance evidence docs:
  - `tests/risk/p0_retry_escalation.md`
  - `tests/integration/p0_supervisor_flow.md`
  - `tests/e2e/p0_trace_visibility.md`
- Verified full unit suite in `llm_gblup` environment with `58 passed`.

### Session 15

- Added human-approval escalation resolution API for practical governance closure:
  - `POST /jobs/{job_id}/escalation/retry`
  - `POST /jobs/{job_id}/escalation/abort`
- Extended job state contract for escalation resolution audit:
  - `escalation_resolution`
  - `escalation_resolved_by`
  - `escalation_resolved_at`
- Implemented escalation resolution behaviors:
  - retry approval clears escalation and re-queues job (auto enqueue in async mode)
  - abort approval marks job failed with `manual_abort_after_escalation`
  - both actions append explicit decision-trace override nodes
- Added unit API coverage:
  - `tests/unit/api/test_job_escalation.py`
- Added acceptance evidence docs for P1 human-gate items:
  - `tests/risk/p1_approval_gate.md`
  - `tests/integration/p1_override_log.md`
- Updated acceptance trace matrix:
  - `F-P1-04-01 / AC-P1-04-01` -> `IN_PROGRESS`
  - `F-P1-04-02 / AC-P1-04-02` -> `IN_PROGRESS`
- Verified full unit suite in `llm_gblup` environment with `61 passed`.

### Session 16

- Added a delivery-level capability baseline and gap plan:
  - `docs/delivery/CAPABILITY_GAP_AND_UPGRADE_PLAN.md`
- Documented implemented vs pending capabilities aligned to:
  - current API/services runtime
  - backlog Feature IDs
  - acceptance closure expectations
- Added a practical execution sequence (Phase A-D) to guide:
  - immediate acceptance closure
  - P0 deep-QC and strategy-agent upgrades
- Updated document navigation map:
  - `docs/delivery/DELIVERY_DOC_MAP.md` now includes the new capability-gap entry.

### Session 17

- Implemented a unified Phase-A acceptance runner for governance-related AC closure:
  - service module: `src/animal_gs_agent/services/acceptance_runner_service.py`
  - CLI wrapper: `scripts/delivery/run_phase_a_acceptance.py`
  - generated evidence file: `tests/integration/phase_a_unified_acceptance_latest.md`
- Added TDD coverage for the new acceptance runner:
  - `tests/unit/services/test_acceptance_runner_service.py`
  - `tests/unit/scripts/test_run_phase_a_acceptance.py`
- Hardened runner interpreter behavior:
  - switched test commands from fixed `python` to `sys.executable` for cluster compatibility.
- Updated delivery governance docs:
  - added unified acceptance execution section in `docs/delivery/ENGINEERING_QA_SOP.md`
  - updated matrix evidence/status for:
    - `AC-P0-01-01`, `AC-P0-01-02`, `AC-P0-01-03`
    - `AC-P1-04-01`, `AC-P1-04-02`

### Session 18

- Started `E-P0-02` practical deep-QC upgrade (`F-P0-02-01` slice):
  - extended dataset profile with genotype missingness summary and QC risk level
  - added PLINK2 missingness report parsing support (`.smiss/.vmiss`) through env paths
  - added threshold-based high-risk flagging (`ANIMAL_GS_AGENT_QC_MISSINGNESS_HIGH_THRESHOLD`, default `0.10`)
- Added pre-run QC risk gate behavior:
  - high-risk jobs are blocked before workflow launch with `execution_error=qc_risk_high_blocked`
  - decision trace records QC gate decision under `F-P0-02-01 / S-P0-02-05`
- Added manual QC override API:
  - `POST /jobs/{job_id}/qc/override`
  - stores audit fields: `qc_override_applied`, `qc_override_by`, `qc_override_reason`, `qc_override_at`
  - appends decision trace action `approve_qc_override`
- Added tests and evidence artifacts:
  - `tests/unit/p0_qc_missingness_test.py`
  - `tests/unit/api/test_job_qc_override.py`
  - `tests/e2e/p0_qc_blocking.md`
  - `tests/risk/p0_override_audit.md`
- Updated delivery docs and matrix:
  - `docs/delivery/AGENT_FULL_PICTURE.md`
  - `docs/delivery/ACCEPTANCE_TRACE_MATRIX.md` (`AC-P0-02-01=PASS`, `AC-P0-02-02/03=IN_PROGRESS`)
- Verified full unit suite with `71 passed`.

### Session 19

- Continued `E-P0-02` with population-structure diagnostics (`F-P0-02-02` slice):
  - added `population_structure` summary in dataset profile
  - added `risk_tags` propagation for structure outliers and high relatedness
  - supported optional PLINK2 inputs:
    - `ANIMAL_GS_AGENT_PLINK2_PCA_EIGENVEC_PATH`
    - `ANIMAL_GS_AGENT_PLINK2_RELATEDNESS_PATH`
  - added thresholds:
    - `ANIMAL_GS_AGENT_QC_PCA_ZSCORE_THRESHOLD`
    - `ANIMAL_GS_AGENT_QC_RELATEDNESS_HIGH_THRESHOLD`
- Improved report explainability:
  - report text now includes active risk tags to distinguish governance decisions from workflow execution.
- Added tests and evidence:
  - `tests/unit/services/test_dataset_profile_service.py` (population structure parsing)
  - `tests/unit/api/test_job_run.py` (risk-tag carry-through into execution stage)
  - `tests/unit/api/test_job_report.py` (risk tags in report text)
  - `tests/integration/p0_population_structure.md`
  - `tests/risk/p0_structure_risk_tag.md`
- Updated trace matrix:
  - `AC-P0-02-04` -> `IN_PROGRESS`
  - `AC-P0-02-05` -> `IN_PROGRESS`

### Session 20

- Continued `E-P0-02` with phenotype outlier and batch-effect diagnostics (`F-P0-02-03` slice):
  - added `phenotype_diagnostics` summary to dataset profile
  - computes outlier ratio using trait-value z-scores
  - computes batch-effect eta2 and significance thresholding
  - emits structured recommendations, including covariate/stratified split guidance
- Added configurable phenotype diagnostics env vars:
  - `ANIMAL_GS_AGENT_PHENO_BATCH_COLUMN`
  - `ANIMAL_GS_AGENT_PHENO_OUTLIER_ZSCORE_THRESHOLD`
  - `ANIMAL_GS_AGENT_PHENO_OUTLIER_HIGH_RATIO_THRESHOLD`
  - `ANIMAL_GS_AGENT_PHENO_BATCH_EFFECT_MIN_ETA2`
- Extended risk-tag propagation:
  - `phenotype_outlier_high`
  - `phenotype_batch_effect_significant`
- Extended report explainability:
  - report now includes `Agent recommendation` line from phenotype diagnostics.
- Added tests and evidence:
  - `tests/unit/services/test_dataset_profile_service.py` (phenotype diagnostics coverage)
  - `tests/unit/api/test_job_report.py` (covariate recommendation in E2E API path)
  - `tests/integration/p0_pheno_batch_diagnosis.md`
  - `tests/e2e/p0_covariate_recommendation.md`
- Updated trace matrix:
  - `AC-P0-02-06` -> `IN_PROGRESS`
  - `AC-P0-02-07` -> `IN_PROGRESS`

### Session 21

- Started `E-P0-03` model-candidate pool slice (`F-P0-03-01`):
  - added model-pool planning schemas:
    - `src/animal_gs_agent/schemas/model_pool.py`
  - added model-pool availability service:
    - `src/animal_gs_agent/services/model_pool_service.py`
  - candidate set currently includes:
    - `GBLUP`
    - `BayesB`
    - `XGBoost`
  - service now emits:
    - `available_models`
    - per-model `disabled_reasons`
- Added and validated unit evidence:
  - `tests/unit/p0_model_pool_availability.py`
- Updated delivery docs/matrix:
  - `docs/delivery/AGENT_FULL_PICTURE.md`
  - `docs/delivery/ACCEPTANCE_TRACE_MATRIX.md` (`AC-P0-03-01=PASS`)
- Verified targeted regression set:
  - `tests/unit/p0_qc_missingness_test.py`
  - `tests/unit/p0_trace_schema_test.py`
  - `tests/unit/services/test_dataset_profile_service.py`
  - `tests/unit/api/test_job_run.py`
  - `tests/unit/api/test_job_report.py`

### Session 22

- Continued `E-P0-03` with trial-orchestration budget guard (`F-P0-03-02`):
  - added trial-strategy schemas:
    - `src/animal_gs_agent/schemas/trial_strategy.py`
  - added budget-constrained trial orchestrator service:
    - `src/animal_gs_agent/services/trial_orchestrator_service.py`
  - implemented core outputs:
    - trial sequence
    - selected model
    - budget consumed
    - stop reason
  - implemented reproducibility behavior:
    - deterministic trial replay under identical `random_seed`
- Added and validated unit evidence:
  - `tests/unit/p0_trial_budget_guard.py`
- Updated delivery docs/matrix:
  - `docs/delivery/AGENT_FULL_PICTURE.md`
  - `docs/delivery/ACCEPTANCE_TRACE_MATRIX.md` (`AC-P0-03-03=PASS`)

### Session 23

- Continued `E-P0-03` model-pool execution-planning visibility (`F-P0-03-01`):
  - extended job contracts with model-pool field:
    - `model_pool_plan` in `JobSubmissionResponse`
    - `model_pool_plan` in `JobStatusResponse`
  - wired model-pool planning into job creation:
    - `create_job(...)` now computes and persists plan from task + dataset profile
- Added API-level verification for rejection reasons:
  - `tests/unit/api/test_job_submission.py::test_submit_job_includes_model_pool_disable_reasons`
- Added integration evidence doc:
  - `tests/integration/p0_model_pool_rejection_reason.md`
- Updated delivery docs/matrix:
  - `docs/delivery/AGENT_FULL_PICTURE.md`
  - `docs/delivery/ACCEPTANCE_TRACE_MATRIX.md` (`AC-P0-03-02=PASS`)

### Session 24

- Continued `E-P0-03` strategy-stop transparency and reproducibility closure (`F-P0-03-02`):
  - extended job contracts with trial strategy field:
    - `trial_strategy_plan` in `JobSubmissionResponse`
    - `trial_strategy_plan` in `JobStatusResponse`
  - wired trial strategy planning into job creation with configurable inputs:
    - `ANIMAL_GS_AGENT_STRATEGY_MAX_TRIALS`
    - `ANIMAL_GS_AGENT_STRATEGY_EARLY_STOP_PATIENCE`
    - `ANIMAL_GS_AGENT_STRATEGY_MIN_IMPROVEMENT`
    - `ANIMAL_GS_AGENT_STRATEGY_RANDOM_SEED`
- Added API-level verification:
  - `tests/unit/api/test_job_submission.py::test_submit_job_includes_trial_stop_reason`
- Added acceptance evidence docs:
  - `tests/e2e/p0_early_stop_reason.md`
  - `tests/risk/p0_reproducibility_seed.md`
- Updated delivery docs/matrix:
  - `docs/delivery/AGENT_FULL_PICTURE.md`
  - `docs/delivery/ACCEPTANCE_TRACE_MATRIX.md` (`AC-P0-03-04=PASS`, `AC-P0-03-05=PASS`)

### Session 25

- Continued `E-P0-03` scene-specific validation protocol closure (`F-P0-03-03`):
  - added validation protocol schemas:
    - `src/animal_gs_agent/schemas/validation_protocol.py`
  - added scenario validation protocol service:
    - `src/animal_gs_agent/services/validation_protocol_service.py`
  - attached validation protocol planning to job state:
    - `validation_protocol_plan` in `JobSubmissionResponse`
    - `validation_protocol_plan` in `JobStatusResponse`
  - scenarios covered:
    - `within_pop`
    - `cross_pop`
  - metrics emitted:
    - `within_pop_pearson`
    - `within_pop_rmse`
    - `cross_pop_pearson`
    - `cross_pop_rmse`
- Added verification evidence:
  - `tests/unit/services/test_job_service_practical.py::test_create_job_attaches_validation_protocol_plan`
  - `tests/integration/p0_within_pop_protocol.md`
  - `tests/integration/p0_cross_pop_protocol.md`
- Updated delivery docs/matrix:
  - `docs/delivery/AGENT_FULL_PICTURE.md`
  - `docs/delivery/ACCEPTANCE_TRACE_MATRIX.md` (`AC-P0-03-06=PASS`, `AC-P0-03-07=PASS`)

### Session 26

- Started `E-P0-04` audit-agent claim-evidence slice (`F-P0-04-01`):
  - added audit claim schema:
    - `src/animal_gs_agent/schemas/audit_claim.py`
  - added audit service:
    - `src/animal_gs_agent/services/audit_service.py`
  - report now includes claim-evidence output:
    - `claim_evidence_map` in `JobReportResponse`
    - populated by `build_job_report(...)`
- Added and verified tests:
  - `tests/unit/p0_claim_evidence_map.py`
    - evidence binding acceptance check
    - reject path when evidence is missing
- Added risk evidence doc:
  - `tests/risk/p0_reject_no_evidence.md`
- Updated delivery docs/matrix:
  - `docs/delivery/AGENT_FULL_PICTURE.md`
  - `docs/delivery/ACCEPTANCE_TRACE_MATRIX.md` (`AC-P0-04-01=PASS`, `AC-P0-04-02=PASS`)

### Session 27

- Continued `E-P0-04` leakage + metric-consistency audit slice (`F-P0-04-02`):
  - added structured audit verdict schema:
    - `AuditCheckResult` in `src/animal_gs_agent/schemas/audit_claim.py`
  - extended audit service:
    - `run_audit_checks(...)` emits:
      - `leakage_check`
      - `metric_consistency_check`
  - report response now includes:
    - `audit_checks` in `JobReportResponse`
- Added verification:
  - `tests/unit/p0_claim_evidence_map.py::test_audit_checks_detect_leakage_and_metric_conflict`
- Added integration evidence docs:
  - `tests/integration/p0_leakage_check.md`
  - `tests/integration/p0_metric_consistency.md`
- Updated delivery docs/matrix:
  - `docs/delivery/AGENT_FULL_PICTURE.md`
  - `docs/delivery/ACCEPTANCE_TRACE_MATRIX.md` (`AC-P0-04-03=PASS`, `AC-P0-04-04=PASS`)

### Session 28

- Started `E-P0-05` metric unification slice (`F-P0-05-01`):
  - added metric schemas:
    - `src/animal_gs_agent/schemas/metric.py`
  - added metric service:
    - `src/animal_gs_agent/services/metric_service.py`
  - capabilities:
    - trial-level `Pearson` and `RMSE`
    - grouped aggregate metrics by `(population, trait, model)`
- Added tests:
  - `tests/unit/p0_metric_pearson_rmse.py`
- Updated delivery docs/matrix:
  - `docs/delivery/AGENT_FULL_PICTURE.md`
  - `docs/delivery/ACCEPTANCE_TRACE_MATRIX.md` (`AC-P0-05-01=PASS`)

### Session 29

- Continued `E-P0-05` decision-quality metrics (`F-P0-05-02`):
  - extended metric schema:
    - `DecisionQualityResult` in `src/animal_gs_agent/schemas/metric.py`
  - extended metric service:
    - `compute_decision_quality(...)` for:
      - `top1_hit`
      - `regret`
      - missing-oracle fallback reason
- Added tests:
  - `tests/unit/p0_top1_regret.py`
- Added evidence docs:
  - `tests/integration/p0_metric_aggregation.md`
  - `tests/integration/p0_top1_regret.md`
  - `tests/risk/p0_oracle_missing.md`
- Updated delivery docs/matrix:
  - `docs/delivery/AGENT_FULL_PICTURE.md`
  - `docs/delivery/ACCEPTANCE_TRACE_MATRIX.md` (`AC-P0-05-02=PASS`, `AC-P0-05-03=PASS`, `AC-P0-05-04=PASS`)

### Session 30

- Completed `E-P0-05` search-efficiency metrics (`F-P0-05-03`):
  - extended metric schema:
    - `SearchEfficiencyResult` in `src/animal_gs_agent/schemas/metric.py`
  - extended metric service:
    - `compute_search_efficiency(...)` for:
      - `trials_to_95_best`
      - `invalid_trial_rate`
      - invalid reason breakdown
      - `no_valid_trials` fallback
- Added tests:
  - `tests/unit/p0_search_efficiency.py`
- Added evidence docs:
  - `tests/integration/p0_trials_to_95.md`
  - `tests/integration/p0_invalid_trial_rate.md`
- Updated delivery docs/matrix:
  - `docs/delivery/AGENT_FULL_PICTURE.md`
  - `docs/delivery/ACCEPTANCE_TRACE_MATRIX.md` (`AC-P0-05-05=PASS`, `AC-P0-05-06=PASS`)

### Session 31

- Closed remaining `E-P0-02` acceptance rows by verification sweep:
  - `F-P0-02-01`: `AC-P0-02-02`, `AC-P0-02-03`
  - `F-P0-02-02`: `AC-P0-02-04`, `AC-P0-02-05`
  - `F-P0-02-03`: `AC-P0-02-06`, `AC-P0-02-07`
- Verified with targeted unit/API checks:
  - `tests/unit/api/test_job_qc_override.py::test_qc_override_requeues_blocked_job`
  - `tests/unit/api/test_job_run.py::test_run_job_blocks_before_workflow_when_qc_risk_is_high`
  - `tests/unit/api/test_job_run.py::test_run_job_carries_population_risk_tags_into_execution_stage`
  - `tests/unit/api/test_job_report.py::test_job_report_includes_covariate_recommendation_when_batch_effect_significant`
  - `tests/unit/services/test_dataset_profile_service.py::test_build_dataset_profile_parses_population_structure_and_outliers`
  - `tests/unit/services/test_dataset_profile_service.py::test_build_dataset_profile_generates_phenotype_outlier_and_batch_diagnostics`
- Updated delivery matrix:
  - `docs/delivery/ACCEPTANCE_TRACE_MATRIX.md`
  - set `AC-P0-02-02`..`AC-P0-02-07` to `PASS`

### Session 32

- Implemented `E-P1-01` knowledge-agent slice:
  - `F-P1-01-01` knowledge connector
  - `F-P1-01-02` retrieval + rerank
  - `F-P1-01-03` citation conflict annotation
- Added schemas:
  - `src/animal_gs_agent/schemas/knowledge.py`
    - `KnowledgeDocument`
    - `RetrievedEvidence`
    - `RecommendationCitation`
- Added knowledge service:
  - `src/animal_gs_agent/services/knowledge_service.py`
    - `build_knowledge_documents(...)`
    - `retrieve_knowledge_evidence(...)`
    - `build_recommendation_citations(...)`
- Extended report schema/service:
  - `knowledge_citations` in `JobReportResponse`
  - report generation now attaches recommendation citations and conflict notes
- Added tests:
  - `tests/unit/p1_knowledge_rag.py`
  - `tests/unit/api/test_job_report.py::test_job_report_includes_knowledge_citations`
- Added evidence docs:
  - `tests/integration/p1_knowledge_connector.md`
  - `tests/integration/p1_retrieval_rerank.md`
  - `tests/risk/p1_evidence_conflict.md`
- Updated delivery docs/matrix:
  - `docs/delivery/AGENT_FULL_PICTURE.md`
  - `docs/delivery/ACCEPTANCE_TRACE_MATRIX.md` (`AC-P1-01-01=PASS`, `AC-P1-01-02=PASS`, `AC-P1-01-03=PASS`)

### Session 33

- Implemented `E-P1-02` badcase memory loop slice:
  - `F-P1-02-01` badcase schema
  - `F-P1-02-02` similarity retrieval
  - `F-P1-02-03` preventive-action generation
- Added schemas:
  - `src/animal_gs_agent/schemas/badcase.py`
    - `BadcaseRecord`
    - `SimilarBadcaseMatch`
    - `BadcaseAdvice`
- Added service:
  - `src/animal_gs_agent/services/badcase_service.py`
    - `build_badcase_record(...)`
    - `build_badcase_advice(...)`
    - composite similarity scoring + risk/action mapping
- Extended job creation:
  - `create_job(...)` now queries historical badcases before run
  - output attached as `badcase_advice` in `JobSubmissionResponse` / `JobStatusResponse`
- Added tests:
  - `tests/unit/p1_badcase_schema.py`
  - `tests/unit/services/test_job_service_practical.py::test_create_job_queries_historical_badcase_and_emits_preventive_actions`
- Added evidence docs:
  - `tests/integration/p1_badcase_similarity.md`
  - `tests/e2e/p1_preventive_actions.md`
- Updated delivery docs/matrix:
  - `docs/delivery/AGENT_FULL_PICTURE.md`
  - `docs/delivery/ACCEPTANCE_TRACE_MATRIX.md` (`AC-P1-02-01=PASS`, `AC-P1-02-02=PASS`, `AC-P1-02-03=PASS`)

### Session 34

- Implemented `E-P1-03` multi-role report templates:
  - report schema extended with:
    - `role_reports`
    - `role_report_alignment_ok`
    - `role_report_alignment_note`
  - role reports generated for:
    - `technical`
    - `decision`
    - `management`
  - all role reports share one final conclusion and each includes audit/risk summaries
- Implemented `F-P1-04-03` forced-abort rollback output:
  - job schema extended with `fallback_plan`
  - escalation abort now writes fallback metadata:
    - strategy: `manual_review_with_fixed_pipeline_fallback`
    - reason/approver/timestamp
- Added tests:
  - `tests/unit/api/test_job_report.py::test_job_report_includes_role_specific_reports_with_consistent_conclusion`
  - `tests/unit/api/test_job_escalation.py::test_abort_escalated_job_records_manual_abort`
- Added evidence docs:
  - `tests/integration/p1_technical_report.md`
  - `tests/integration/p1_decision_report.md`
  - `tests/integration/p1_management_report.md`
  - `tests/e2e/p1_abort_and_fallback.md`
- Updated delivery docs/matrix:
  - `docs/delivery/AGENT_FULL_PICTURE.md`
  - `docs/delivery/ACCEPTANCE_TRACE_MATRIX.md`
    - `AC-P1-03-01=PASS`
    - `AC-P1-03-02=PASS`
    - `AC-P1-03-03=PASS`
    - `AC-P1-04-03=PASS`

### Session 35

- Implemented `E-P2-02` debug-agent baseline:
  - `F-P2-02-01` failure classifier
  - `F-P2-02-02` repair suggestion + retry policy
  - `F-P2-02-03` escalation stop logic
- Added schemas:
  - `src/animal_gs_agent/schemas/debug.py`
    - `DebugDiagnosis`
- Added service:
  - `src/animal_gs_agent/services/debug_service.py`
    - `classify_failure_category(...)`
    - `build_debug_diagnosis(...)`
    - `should_escalate_after_attempt(...)`
- Integrated into runtime:
  - `JobSubmissionResponse` / `JobStatusResponse` now expose `debug_diagnosis`
  - `run_job(...)` now attaches `debug_diagnosis` for:
    - preflight validation failures
    - workflow runtime failures
    - workflow output parse failures
- Added tests:
  - `tests/unit/p2_failure_classifier.py`
  - `tests/unit/api/test_job_run.py::test_run_job_transitions_to_failed_when_workflow_runtime_errors`
- Added evidence docs:
  - `tests/integration/p2_retry_policy.md`
  - `tests/risk/p2_escalation_stop.md`
- Updated delivery docs/matrix:
  - `docs/delivery/AGENT_FULL_PICTURE.md`
  - `docs/delivery/ACCEPTANCE_TRACE_MATRIX.md`
    - `AC-P2-02-01=PASS`
    - `AC-P2-02-02=PASS`
    - `AC-P2-02-03=PASS`

### Session 36

- Implemented `E-P2-01` benchmark and ablation workbench:
  - `F-P2-01-01` baseline benchmark orchestrator
  - `F-P2-01-02` ablation benchmark orchestrator
  - `F-P2-01-03` plot-ready artifact export
- Added schemas:
  - `src/animal_gs_agent/schemas/benchmark.py`
    - baseline arm result
    - ablation item
    - plot export artifact
- Added service:
  - `src/animal_gs_agent/services/benchmark_service.py`
    - `build_baseline_benchmark(...)`
    - `build_ablation_benchmark(...)`
    - `export_plot_artifact(...)`
- Report integration:
  - `JobReportResponse` now includes:
    - `benchmark_baseline`
    - `benchmark_ablation`
    - `benchmark_plot_artifact`
  - report service now builds and attaches all benchmark outputs
- Added tests:
  - `tests/unit/p2_benchmark_service.py`
  - `tests/unit/api/test_job_report.py::test_job_report_includes_benchmark_and_plot_export`
- Added evidence docs:
  - `tests/integration/p2_baseline_bench.md`
  - `tests/integration/p2_ablation_bench.md`
  - `tests/e2e/p2_plot_export.md`
- Updated delivery docs/matrix:
  - `docs/delivery/AGENT_FULL_PICTURE.md`
  - `docs/delivery/ACCEPTANCE_TRACE_MATRIX.md`
    - `AC-P2-01-01=PASS`
    - `AC-P2-01-02=PASS`
    - `AC-P2-01-03=PASS`

### Session 37

- Implemented `E-P2-03` platform governance baseline:
  - `F-P2-03-01` scope authorization
  - `F-P2-03-02` quota gate
  - `F-P2-03-03` observability audit endpoint
- Added schemas/services:
  - `src/animal_gs_agent/schemas/governance.py`
  - `src/animal_gs_agent/services/governance_service.py`
- Extended job request/status metadata:
  - `requested_by`
  - `project_scope`
  - `access_scopes`
- API/flow integration:
  - `POST /jobs` now enforces:
    - scope check (`403 authz_scope_denied`)
    - quota check (`429 project_quota_exceeded`)
  - added governance audit API:
    - `GET /jobs/{job_id}/governance/audit`
- Added tests:
  - `tests/unit/api/test_governance_controls.py`
- Added evidence docs:
  - `tests/integration/p2_authz_scope.md`
  - `tests/integration/p2_quota_control.md`
  - `tests/e2e/p2_observability_audit.md`
- Updated delivery docs/matrix:
  - `docs/delivery/AGENT_FULL_PICTURE.md`
  - `docs/delivery/ACCEPTANCE_TRACE_MATRIX.md`
    - `AC-P2-03-01=PASS`
    - `AC-P2-03-02=PASS`
    - `AC-P2-03-03=PASS`

### Session 38

- Added software-style CLI packaging for cross-directory invocation:
  - new command entrypoint:
    - `gsagent` -> `src/animal_gs_agent/cli.py`
  - core subcommands:
    - `preflight`
    - `serve`
    - `worker`
    - `print-env`
  - supports explicit runtime binding:
    - `--workdir <target-dir>`
    - optional `.env` loading per workdir
- Added Python package script registration:
  - `pyproject.toml` `[project.scripts]`
- Added runtime bundle packaging helpers:
  - `packaging/runtime/build_cli_runtime_bundle.sh`
  - `packaging/runtime/install_runtime.sh`
  - `packaging/runtime/README.md`
- Updated docs:
  - `README.md` with CLI installation and usage
  - `docs/delivery/AGENT_FULL_PICTURE.md` with CLI software mode
- Added tests:
  - `tests/unit/test_cli.py`

### Session 39

- Extended CLI startup UX with PM-style interactive LLM readiness gate:
  - added subcommand:
    - `gsagent llm-check`
  - `gsagent serve` now supports startup LLM check modes:
    - `--llm-check auto|always|skip`
    - default `auto` asks user whether to run check
  - user-input flow during check:
    - prompts missing `base_url/api_key/model`
    - prompts probe message (default `ping`)
  - failed check blocks service startup with explicit reason
- Updated docs:
  - `README.md`
  - `packaging/runtime/README.md`

### Session 40

- Added global command installer for newcomer-friendly setup:
  - `scripts/install_global_gsagent.sh`
  - installs `gsagent` into `~/.local/bin/gsagent`
  - includes PATH warning guidance if `~/.local/bin` is not exported
- Updated docs with global installation path:
  - `README.md`
  - `packaging/runtime/README.md`
