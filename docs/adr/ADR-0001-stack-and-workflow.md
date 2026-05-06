# ADR-0001: LangGraph Agent With Fixed One-Stage GBLUP Workflow

## Status

Accepted

## Context

The project needs to demonstrate a clear difference between an intelligent agent and a static workflow while staying practical enough for a company-facing MVP. The available data currently includes animal genotype data and raw phenotype data, but no pedigree data.

## Decision

Use:

- `LangGraph` as the agent orchestration layer
- a fixed one-stage `GBLUP` workflow as the statistical core
- `PLINK 2` for genotype QC
- `BLUPF90+` as the default evaluation engine
- `FastAPI` plus `Celery` plus `Redis` for service execution

## Rationale

- `LangGraph` provides explicit graph state, durable execution, and clearer agent-vs-workflow boundaries than a thin chat wrapper.
- Without pedigree, the MVP should not claim to implement `ssGBLUP`.
- A fixed GBLUP core is easier to validate, easier to explain, and easier to operate than allowing an LLM to improvise statistical pipelines.
- The agent's value should be concentrated in task understanding, data readiness checks, parameter guardrails, and breeding-oriented interpretation.

## Consequences

- The initial version will prioritize traceability and robustness over model breadth.
- Bayesian or alternative models can be added later as challenger workflows.
- If pedigree becomes available later, the system can evolve toward `ssGBLUP` without replacing the surrounding service architecture.

