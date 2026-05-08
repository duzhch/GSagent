# Capability Gap and Upgrade Plan

Last updated: 2026-05-08

## 1. Purpose

This document defines:

- what is already implemented in the current agent
- what still needs to be built
- what to execute next in practical priority order

It is the execution bridge between:

- `AGENT_FULL_PICTURE.md` (technical snapshot)
- `REQ_BACKLOG_FILLED.md` (full requirement universe)
- `ACCEPTANCE_TRACE_MATRIX.md` (test/evidence closure status)

## 2. Existing Capabilities (Implemented or Partially Implemented)

## 2.1 Core MVP Runtime (Implemented)

1. Task understanding through model API (`POST /agent/parse-task`) with strict no-fallback behavior.
2. Job lifecycle APIs (`POST /jobs`, `POST /jobs/{id}/run`, `GET /jobs/{id}`).
3. Dataset profiling and contract checks for genotype/phenotype inputs.
4. Fixed GS workflow execution via Nextflow backend.
5. Result parsing and breeding-oriented report generation:
   - `GET /jobs/{id}/report`
   - `GET /jobs/{id}/artifacts`
6. Structured job events and machine-readable error codes.

Reference:
- `src/animal_gs_agent/api/routes/jobs.py`
- `src/animal_gs_agent/services/workflow_service.py`
- `src/animal_gs_agent/services/workflow_result_service.py`
- `src/animal_gs_agent/services/report_service.py`

## 2.2 Cluster Practicality (Implemented)

1. Slurm-aware execution policy (`auto|local|slurm`) for login-node safety.
2. Slurm submit mode with `workflow_submission_id`.
3. Slurm state refresh on job status query.

Reference:
- `src/animal_gs_agent/services/slurm_service.py`
- `src/animal_gs_agent/services/workflow_service.py`

## 2.3 Persistence and Async Worker (Implemented)

1. Optional JSON/SQLite job-state persistence.
2. Optional SQLite async queue mode.
3. Worker control-plane APIs:
   - `GET /worker/health`
   - `POST /worker/process-once`
   - `GET /worker/queue/{job_id}`

Reference:
- `src/animal_gs_agent/services/job_service.py`
- `src/animal_gs_agent/services/run_queue_service.py`
- `src/animal_gs_agent/services/worker_service.py`

## 2.4 Agent Governance and Audit (Partially Implemented)

Already implemented:
1. Standardized decision trace schema and trace replay API (`GET /jobs/{id}/trace`).
2. Retry budget governance with dead-letter escalation.
3. Escalation approval APIs:
   - `POST /jobs/{id}/escalation/retry`
   - `POST /jobs/{id}/escalation/abort`
4. Escalation audit fields and decision-trace override logs.

Still pending for full closure:
1. Multi-agent graph runtime with real data-agent/model-agent/audit-agent node boundaries.
2. Broader governance AC closure in unified QA replay.

Reference:
- `src/animal_gs_agent/schemas/jobs.py`
- `src/animal_gs_agent/services/job_service.py`
- `tests/risk/p1_approval_gate.md`
- `tests/integration/p1_override_log.md`

## 3. New Capabilities To Build (By Priority)

## 3.1 P0 Must-Build (High Impact, Demo + Practical Utility)

### A. E-P0-02 Data-Agent Deep QC

Missing capabilities:
1. Sample/marker-level missingness statistics endpoint outputs.
2. Population structure diagnostics (PCA + outlier list).
3. Relatedness warnings.
4. Phenotype outlier and batch-effect diagnostics.
5. Risk grading and default blocking with auditable override flow.

Why now:
1. Directly improves real animal phenotype/genotype usability.
2. Best demonstration of “agent decision” over plain workflow execution.

### B. E-P0-03 Model-Agent Strategy Search

Missing capabilities:
1. Candidate model registry (`GBLUP`, `BayesB`, `XGBoost`) with availability reasons.
2. Trial orchestrator under `max_trials`.
3. Early-stop reason persistence.
4. Reproducibility seed policy and replay.
5. Within-pop and cross-pop protocol records.

Why now:
1. This is the strongest perceptual difference between “workflow runner” and “intelligent agent”.

### C. E-P0-04 Audit-Agent Core Rules

Missing capabilities:
1. Claim-evidence validator.
2. Leakage checker.
3. Metric consistency checker.
4. Verdict API (`accept/reject/risk`).

Why now:
1. Needed for high-standard output credibility and enterprise review readiness.

### D. E-P0-05 Productized Metrics

Missing capabilities:
1. Pearson/RMSE unified metric output.
2. Top-1 hit and Regret outputs.
3. Efficiency metrics (`Trials-to-95%-Best`, `Invalid Trial Rate`).
4. Aggregate metrics API for demo and weekly reporting.

Why now:
1. Converts outcomes into measurable business/research value.

## 3.2 P1 Next-Wave (After P0 Core Closure)

1. `E-P1-01` Knowledge agent (RAG + citation/conflict signals).
2. `E-P1-02` Badcase memory loop (historical risk recall before run).
3. `E-P1-03` Multi-role reporting (technical/decision/management views).
4. `E-P1-04` currently partial; finish E2E branch `AC-P1-04-03`.

## 3.3 P2 Platformization (Later)

1. Comparison and ablation workbench.
2. Debug agent with failure taxonomy and controlled retry playbooks.
3. Platform governance (authz, quota, observability audit).

## 4. Execution Update Sequence (Recommended)

## Phase A (Now): Close P0-01 and P1-04 acceptance loop

1. Add a unified acceptance runner for implemented governance paths.
2. Re-run evidence generation and promote eligible AC rows from `IN_PROGRESS` to `PASS`.

## Phase B: Deliver the first “Agent > Workflow” practical jump

1. Build `E-P0-02` deep QC outputs and risk gate.
2. Wire risk tags into job state, trace, and report.

## Phase C: Make strategy intelligence visible

1. Build model registry + trial orchestration (`E-P0-03`).
2. Persist strategy decisions and early-stop rationale in trace/report.

## Phase D: Build scientific trust closure

1. Implement `E-P0-04` audit checks.
2. Implement `E-P0-05` metric outputs and aggregate view.

## 5. Definition of “Updated and Ready”

A capability is considered done only when all conditions hold:

1. Code implemented with Feature/Story IDs traceable.
2. AC evidence generated and linked in `ACCEPTANCE_TRACE_MATRIX.md`.
3. Development log updated (`docs/changelog/DEVELOPMENT_LOG.md`).
4. Demo/runbook updated for operator replay.
