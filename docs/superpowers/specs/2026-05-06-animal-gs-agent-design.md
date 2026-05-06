# Animal GS Agent Design

**Goal:** Build a packaged MVP for animal-breeding genomic selection that demonstrates agent behavior on top of a fixed, reproducible evaluation workflow.

## Problem Statement

The project needs to show that the system is more than a static workflow launcher. Users should be able to describe a breeding objective in natural language, upload genotype and raw phenotype data, and receive both a stable GBLUP evaluation result and an explanation-oriented recommendation. The MVP must be suitable for demo use while remaining extensible toward real deployment.

## MVP Scope

The MVP includes:

- animal genotype upload and validation
- raw phenotype upload and validation
- fixed-effect candidate detection from phenotype columns
- genotype QC with preconfigured thresholds
- one-stage GBLUP execution
- cross-validation summary
- ranked GEBV output
- agent-generated explanation and breeding recommendation
- packaged local deployment

The MVP excludes:

- pedigree-aware single-step models
- arbitrary user-authored workflows
- free-form shell tool execution
- multi-organization access control
- production cluster scheduling

## Core Product Definition

The system is a domain-constrained animal GS agent:

- the workflow layer performs stable and reproducible computation
- the agent layer interprets user intent, validates inputs, routes execution, and explains results

This separation is the main product distinction from a static workflow portal.

## User Experience

The expected happy path is:

1. User uploads genotype and phenotype files.
2. User asks for a GS evaluation in natural language.
3. The agent checks whether the request matches the supported MVP capability.
4. The agent validates the files, trait column, and candidate fixed-effect columns.
5. The backend launches the fixed GBLUP workflow.
6. The system returns job status, metrics, ranked GEBV output, and a recommendation summary.

## Architecture

### 1. API Layer

`FastAPI` exposes endpoints for:

- dataset upload
- job submission
- job status lookup
- result download
- trace retrieval

### 2. Agent Layer

`LangGraph` orchestrates a bounded state graph:

- request parsing node
- dataset profiling node
- workflow eligibility node
- execution planning node
- result interpretation node

The graph does not generate arbitrary pipelines. It only chooses among safe branches inside the MVP boundary.

### 3. Execution Layer

Long-running jobs execute outside the request-response cycle:

- `Celery` accepts background jobs
- `Redis` carries queue state
- worker processes call `PLINK 2`, `BLUPF90+`, and R scripts

### 4. Data Layer

`PostgreSQL` stores:

- job metadata
- run status
- selected trait and covariate metadata
- output file references
- agent decision traces

### 5. Packaging Layer

`Docker Compose` packages:

- `api`
- `worker`
- `redis`
- `postgres`
- optional `web`

## Fixed GS Workflow

The default workflow is:

1. ingest genotype and phenotype data
2. align animal identifiers
3. profile phenotype columns
4. run genotype QC with preset thresholds
5. assemble fixed-effect design inputs
6. run one-stage GBLUP
7. compute evaluation metrics
8. generate ranked GEBV output
9. generate an explanation-oriented report

## Agent Responsibilities

The agent is responsible for:

- understanding whether the user request is in MVP scope
- detecting missing required inputs
- surfacing risks such as low sample count or weak phenotype definition
- explaining the workflow choice
- translating outputs into breeding-oriented recommendations

The agent is not responsible for:

- inventing a new statistical workflow
- writing or executing arbitrary shell commands
- changing QC thresholds without guardrails

## Error Handling

The system must return explicit, structured errors for:

- missing IDs
- unsupported file formats
- trait column not found
- not enough samples after QC
- workflow execution failure
- report generation failure

The user-facing response should separate:

- actionable user issues
- internal execution issues

## Testing Strategy

The initial implementation should use:

- unit tests for request parsing, validation, and agent routing
- integration tests for workflow job submission and status handling
- contract tests for worker input/output payloads
- smoke tests for packaged local startup

## Maintainability Rules

- keep repository-level architecture decisions in `docs/adr/`
- keep a running engineering log in `docs/changelog/DEVELOPMENT_LOG.md`
- commit each meaningful change separately
- prefer typed contracts between API, agent, and worker modules

## Initial Deliverables

The first deliverable should contain:

- a standalone git repository
- architecture and implementation documents
- a minimal FastAPI service skeleton
- a minimal LangGraph skeleton
- a background worker contract
- Docker Compose packaging scaffolding

