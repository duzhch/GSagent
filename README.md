# Animal GS Agent

MVP repository for an animal breeding genomic selection agent.

## Goal

Build a LangGraph-based agent that can:

- ingest animal genotype and raw phenotype data
- validate whether the dataset is suitable for a genomic selection run
- launch a fixed one-stage GBLUP workflow
- return ranked GEBV results with breeding-oriented explanations

## MVP Boundary

The first version focuses on:

- raw animal phenotypes
- genotype QC via `PLINK 2`
- fixed-effect aware one-stage `GBLUP`
- agent-guided task understanding, validation, and explanation

The first version does not include:

- pedigree-aware `ssGBLUP`
- free-form workflow generation
- arbitrary tool execution
- multi-tenant production security

## Repository Conventions

- design docs live in `docs/superpowers/specs/`
- implementation plans live in `docs/superpowers/plans/`
- architecture decisions live in `docs/adr/`
- change history lives in `docs/changelog/`

Every meaningful change should be tracked by:

1. a git commit
2. an entry in `docs/changelog/DEVELOPMENT_LOG.md`

## Planned Stack

- `FastAPI` for the service API
- `LangGraph` for agent orchestration
- `PostgreSQL` for job metadata
- `Redis` plus `Celery` for background execution
- `PLINK 2` for genotype QC
- `BLUPF90+` for one-stage GBLUP
- `R` for result shaping and report generation
- `Next.js` for the demo UI
- `Docker Compose` for packaging

## Status

Project initialization and architecture planning in progress.

