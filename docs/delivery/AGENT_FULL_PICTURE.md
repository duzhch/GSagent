# Agent Full Picture

This document is the complete technical snapshot of the current `animal_gs_agent`.

## 1. Product Boundary

The system is a constrained animal-breeding GS agent:

- Agent layer: understands task intent, validates inputs, governs execution decisions, explains outputs
- Workflow layer: runs fixed gold-standard GS workflow (not model-generated pipelines)

The agent is intentionally not a free-form bioinformatics command generator.

## 2. Runtime Architecture

## 2.1 API Layer

- Framework: FastAPI
- Core routes:
  - `POST /agent/parse-task`
  - `POST /jobs`
  - `POST /jobs/{job_id}/run`
  - `GET /jobs/{job_id}`
  - `GET /jobs/{job_id}/report`
  - `GET /jobs/{job_id}/artifacts`

## 2.2 State and Storage

- In-memory primary state: `jobs_store` dictionary
- Optional durable state:
  - set `ANIMAL_GS_AGENT_JOB_STORE_PATH` to persist and recover jobs as JSON
  - or set `ANIMAL_GS_AGENT_JOB_STORE_SQLITE_PATH` for SQLite-based persistence
- Job lifecycle:
  - `queued -> running -> completed/failed`
- Event timeline:
  - each state transition appends structured event entries

## 2.3 LLM Task Understanding

- Provider model: OpenAI-compatible chat API
- Hard requirement: no fallback parser when provider is unavailable
- Output contract: typed `TaskUnderstandingResult`

## 2.4 Workflow Execution

- Fixed backend: Nextflow-based gold-standard pipeline
- Input contract:
  - phenotype structured file (CSV/TSV/TXT with trait column)
  - genotype format validation (VCF/BED/PGEN)
- Execution policy:
  - `local`: force native local execution
  - `slurm`: force Slurm submission
  - `auto`: login-node aware decision

## 2.5 Slurm Awareness

- Login-node behavior (policy `auto`):
  - submit workflow via `sbatch` using `ANIMAL_GS_AGENT_SLURM_SUBMIT_SCRIPT`
  - keep job in `running` with `workflow_submission_id`
- Status refresh on `GET /jobs/{id}`:
  - poll with `sacct`, fallback `squeue`
  - map queue states to terminal/non-terminal outcomes
  - auto transition to `completed`/`failed`

## 2.6 Result Parsing and Reporting

- Parse workflow outputs:
  - `gblup/gebv_predictions.csv`
  - `gblup/model_summary.txt`
  - optional `gblup/accuracy_metrics.rds` via `Rscript`
- Persist `workflow_summary` (top candidates + metrics)
- Report endpoint returns explicit Agent-vs-Workflow narrative

## 3. Error Model

- Stable machine-readable error code: `execution_error`
- Human-readable detail: `execution_error_detail`
- Typical categories:
  - input contract failures
  - workflow runtime errors
  - slurm submission errors
  - post-workflow parse errors

## 4. Operational Modes

## 4.1 Demo Mode

- Native packaging bundle (`packaging/native`)
- Fast startup scripts (`scripts/native/*`)
- 10-minute scripted demo flow (`docs/delivery/DEMO_10MIN_SCRIPT.md`)

## 4.2 Practical Mode (Current)

- Real-data contract check scripts included
- Slurm queue-aware run and refresh behavior
- Optional persistent job-state file survives restart
- Idempotent run guard avoids duplicate execution

## 5. Current Limitations

- Durable storage supports JSON and lightweight SQLite, but not yet PostgreSQL-grade multi-process locking strategy
- No independent worker process yet (API process performs orchestration logic)
- No authn/authz layer yet
- No artifact download authorization policy

## 6. Next Upgrade Path

1. Move job persistence from JSON to SQLite/PostgreSQL.
2. Split workflow execution into background worker.
3. Add retry policy and dead-letter handling for failed runs.
4. Add access control and audit fields for multi-user deployment.
5. Add real pig trait golden-case acceptance suite.
