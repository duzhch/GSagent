# Phase A Unified Acceptance Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reproducible Phase-A acceptance runner that executes implemented governance-related checks and emits a single evidence report for QA replay.

**Architecture:** Introduce a small service module that defines fixed acceptance checks and handles execution/report rendering. Add a CLI script wrapper for operators. Keep the implementation deterministic and file-based so it works on login nodes without extra infrastructure.

**Tech Stack:** Python 3.10+, pytest, pathlib, subprocess

---

### Task 1: Acceptance Runner Service

**Files:**
- Create: `tests/unit/services/test_acceptance_runner_service.py`
- Create: `src/animal_gs_agent/services/acceptance_runner_service.py`

- [x] Step 1: Write failing tests for check catalog, runner execution, and markdown report rendering.
- [x] Step 2: Run targeted tests and verify failure because the service module does not exist.
- [x] Step 3: Implement minimal service functions to satisfy tests.
- [x] Step 4: Re-run targeted tests and verify pass.

### Task 2: CLI Entrypoint

**Files:**
- Create: `tests/unit/scripts/test_run_phase_a_acceptance.py`
- Create: `scripts/delivery/run_phase_a_acceptance.py`

- [x] Step 1: Write failing tests for CLI argument parsing and output file creation behavior.
- [x] Step 2: Run targeted tests and verify failure.
- [x] Step 3: Implement CLI with `--output` and `--workdir` options and service invocation.
- [x] Step 4: Re-run targeted tests and verify pass.

### Task 3: Delivery Docs and Traceability

**Files:**
- Modify: `docs/delivery/ACCEPTANCE_TRACE_MATRIX.md`
- Modify: `docs/delivery/ENGINEERING_QA_SOP.md`
- Modify: `docs/changelog/DEVELOPMENT_LOG.md`

- [x] Step 1: Add SOP section describing how to run unified Phase-A acceptance and where evidence lands.
- [x] Step 2: Update trace matrix rows for covered AC items to point to the unified evidence report path and status.
- [x] Step 3: Add development-log entry for this session.

### Task 4: Verification and Git

**Files:**
- Modify: none (verification only)

- [x] Step 1: Run targeted tests for new service + CLI.
- [x] Step 2: Run `pytest tests/unit -q`.
- [ ] Step 3: Commit with Feature/Story mapping message.
- [ ] Step 4: Push to `origin/main`.
