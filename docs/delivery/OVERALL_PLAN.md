# Overall Plan (Demo + Practical MVP)

This plan is the current master roadmap for the animal breeding GS agent.

## 1. Objective

Build a Slurm-ready, reproducible genomic-selection agent that:

- demonstrates the clear boundary between `Agent` and `Workflow`
- can run real animal phenotype/genotype tasks under common cluster constraints
- is maintainable for post-demo production hardening

## 2. Current Status (Completed)

- Agent task understanding API (`/agent/parse-task`) with model-backed structured parsing
- Job lifecycle APIs (`/jobs`, `/jobs/{id}`, `/jobs/{id}/run`)
- Report API (`/jobs/{id}/report`) with explicit Agent-vs-Workflow explanation text
- Artifacts API (`/jobs/{id}/artifacts`) for reproducibility evidence
- Dataset profiling and input contract validation
- Native workflow execution integration (Nextflow-based fixed GS pipeline)
- Slurm-aware login-node routing policy:
  - auto local/slurm decision
  - submission mode with persisted `workflow_submission_id`
  - status refresh from Slurm queue on `/jobs/{id}`
- Native packaging bundle and delivery docs

## 3. Remaining Work Packages

## WP-A: Slurm End-to-End Observability

Goal:
- Improve queue-state fidelity from submit to finish.

Tasks:
- Expand Slurm state mapping (array jobs and retry states)
- Add optional polling interval policy and state transition throttling
- Persist queue-state history snapshots for audit

Acceptance:
- A submitted job shows stable `running -> completed/failed` transitions without manual intervention.

## WP-B: Real Data Operational Path

Goal:
- Make real pig datasets executable with minimum manual preprocessing.

Tasks:
- Add helper for BED/PGEN to VCF conversion when workflow backend requires VCF input
- Add phenotype/covariate merge helper for multi-file traits
- Add one real-data golden example under documented runbook

Acceptance:
- One pig trait can be submitted, executed, and reported end-to-end on cluster.

## WP-C: Demo Reliability Pack

Goal:
- Ensure a 10-minute demo can be repeated with low failure risk.

Tasks:
- Freeze demo input paths and trait
- Add smoke script to validate API + workflow + artifacts before demo
- Add fallback demo branch (already completed job replay) in case cluster queue delays

Acceptance:
- Demo script executes in predictable sequence with clear operator instructions.

## WP-D: Practical Hardening (Post-Demo)

Goal:
- Transition from in-memory MVP to service-grade baseline.

Tasks:
- Replace in-memory jobs store with persistent storage
- Add background worker process and idempotent run semantics
- Add authentication and audit metadata

Acceptance:
- Service restarts do not lose job states or reports.

## 4. Milestone Timeline

- M1 (now): demo-ready MVP with Slurm-aware routing and traceable outputs
- M2: real-data one-trait operational proof on cluster
- M3: reliability hardening for repeated internal usage
- M4: persistent service foundation for company integration

## 5. Risks and Controls

- Queue delay risk:
  - control: show `workflow_submission_id` and live queue-state polling
- Input-format mismatch risk:
  - control: pre-run contract check + conversion helper scripts
- API provider instability risk:
  - control: strict error visibility, no silent fallback

## 6. Ownership and Handoff

- Engineering change log: `docs/changelog/DEVELOPMENT_LOG.md`
- Acceptance checklist: `docs/delivery/MVP_ACCEPTANCE_CHECKLIST.md`
- Real-data execution guide: `docs/delivery/REAL_DATA_RUNBOOK.md`
- Demo operation script: `docs/delivery/DEMO_10MIN_SCRIPT.md`
