# Development Strategy

## Purpose

This document explains the current development direction and the intended follow-up path for the `animal_gs_agent` repository. It is written to make later maintenance, extension, and handoff easier.

## Product Positioning

The project is not a general-purpose bioinformatics chatbot.

It is a domain-constrained animal breeding genomic selection agent with:

- a fixed and reproducible statistical workflow
- an explicit agent layer for understanding, checking, routing, and explaining

The core distinction from a pure workflow system is:

- workflow computes
- agent interprets and governs

## Current Development Principle

The repository is being built with four constraints:

1. `Demo first`
The first version must be easy to show to supervisors and company stakeholders.

2. `Useful enough to evolve`
Even the MVP must run a real analysis path and not just simulate output.

3. `Constrained intelligence`
The LLM is not allowed to invent arbitrary pipelines or free-form shell commands.
Its role is limited to bounded decisions inside a guarded workflow.

4. `Maintainable growth`
The codebase should be easy to extend toward real deployment without rewriting the whole stack.

## Why This Architecture

### 1. Why LangGraph

`LangGraph` is used because the project needs a visible and inspectable state flow.

That makes it easier to:

- show the difference between agent behavior and workflow execution
- add decision nodes later
- record reasoning traces
- support future human-in-the-loop review points

### 2. Why a fixed GBLUP workflow

The project currently has:

- genotype data
- raw animal phenotype data
- no pedigree data

Because of that, the MVP should not claim to implement `ssGBLUP`.
The stable baseline is a fixed one-stage `GBLUP` workflow.

This keeps the system:

- statistically honest
- easier to debug
- easier to explain
- easier to compare with future upgrades

### 3. Why not let the LLM choose everything

If the model is allowed to freely choose models, QC logic, or shell commands, the system becomes:

- hard to validate
- hard to reproduce
- hard to trust

That would weaken both the demo value and the scientific value.

So the design uses:

- fixed workflow backbone
- bounded agent decisions
- typed API and worker contracts

## Current Build Direction

The current implementation order is:

1. repository standards and documentation
2. FastAPI service skeleton
3. LangGraph intake skeleton
4. job submission contract
5. worker contract
6. packaging scaffold
7. fixed workflow integration
8. result explanation layer
9. front-end demo

This order is intentional.

The goal is to lock down interfaces first, then attach the heavier workflow machinery.

## What the Agent Will Do

In the MVP, the agent is responsible for:

- understanding whether the user request is inside supported scope
- identifying the requested trait
- checking whether required data inputs are present
- checking whether the dataset is structurally usable
- routing the request into the fixed workflow
- translating outputs into breeding-oriented explanations

## What the Agent Will Not Do

In the MVP, the agent will not:

- generate arbitrary pipelines
- choose among many unrelated genomic models
- run arbitrary shell commands
- rewrite scientific logic on the fly
- act as a full autonomous research scientist

This boundary is deliberate and should be preserved unless later requirements change.

## Fixed Workflow Roadmap

### MVP workflow

The first fixed workflow should be:

1. input validation
2. animal ID alignment
3. phenotype column profiling
4. genotype QC
5. fixed-effect design assembly
6. one-stage GBLUP run
7. evaluation metrics
8. ranked GEBV output
9. explanation-oriented report

### Later upgrade path

After the MVP is stable, the workflow can be extended in this order:

1. richer fixed-effect templates for animal phenotypes
2. stronger QC profiling and data diagnostics
3. alternative comparison models such as Bayesian challengers
4. report visualization
5. pedigree-aware upgrade toward `ssGBLUP`
6. cluster execution and larger-scale deployment

## Repository Growth Strategy

The codebase should grow in four layers:

### Layer 1: Interface layer

- FastAPI routes
- request and response schemas
- upload and status APIs

### Layer 2: Agent layer

- LangGraph state definitions
- request classification
- workflow eligibility checks
- explanation assembly

### Layer 3: Execution layer

- background jobs
- worker payloads
- PLINK2 and BLUPF90+ adapters
- report generation

### Layer 4: Packaging layer

- Docker Compose
- environment templates
- runtime configuration
- deployment scripts

Each layer should expose typed contracts to the next.

## Testing Strategy

Development should continue using small TDD cycles:

- write a failing test
- confirm the failure is correct
- implement the smallest possible code
- rerun the test
- commit

Tests should be layered as:

- unit tests for API and agent logic
- integration tests for job execution flow
- smoke tests for local packaged startup

## Documentation Strategy

To keep the project maintainable, every significant change should leave traces in three places:

1. `git commit`
2. `docs/changelog/DEVELOPMENT_LOG.md`
3. `docs/adr/` when the architecture changes

This means later upgrades should not only change code. They should also update the reasoning record.

## Immediate Next Steps

The next coding steps are:

1. add the `/jobs` submission contract
2. add job schemas and a minimal job service
3. add a traceable background-execution placeholder
4. add packaging scaffold files

## Long-Term Direction

The long-term goal is to evolve this repository from:

`demo-grade animal GS agent`

into:

`maintainable animal breeding decision-support platform`

without changing the core idea:

- constrained agent
- reproducible workflow
- explainable breeding output

