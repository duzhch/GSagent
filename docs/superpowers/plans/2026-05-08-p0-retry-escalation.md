# P0 Retry Escalation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `F-P0-01-01 / AC-P0-01-02` so failed worker runs retry under budget, then escalate to dead-letter and stop blind retries.

**Architecture:** Extend SQLite run queue into a governed retry state machine. Worker consumes pending items, records attempt failures, requeues with bounded retry, and marks dead-letter once max-attempts is exceeded. Expose queue record for audit and acceptance evidence.

**Tech Stack:** FastAPI, Pydantic, SQLite, pytest

---

### Task 1: Queue Retry State Machine

**Files:**
- Modify: `src/animal_gs_agent/services/run_queue_service.py`
- Test: `tests/unit/services/test_run_queue_service.py`

- [ ] Add failing tests for:
  - failed attempt under budget requeues as `pending`
  - failed attempt over budget transitions to `dead` and marks escalation
- [ ] Implement queue schema extensions (`max_attempts`, `next_retry_at`, `escalated`, `escalation_reason`) and retry decision function.
- [ ] Verify targeted queue tests pass.

### Task 2: Worker Escalation Behavior

**Files:**
- Modify: `src/animal_gs_agent/services/worker_service.py`
- Test: `tests/unit/services/test_worker_service.py`

- [ ] Add failing worker test that simulates repeated workflow failure and expects final `dead` queue status.
- [ ] Implement worker failure handling using queue retry decision.
- [ ] Verify worker tests pass.

### Task 3: Queue Observability API

**Files:**
- Modify: `src/animal_gs_agent/schemas/worker.py`
- Modify: `src/animal_gs_agent/services/worker_service.py`
- Modify: `src/animal_gs_agent/api/routes/worker.py`
- Test: `tests/unit/api/test_worker_routes.py`

- [ ] Add failing API test for `GET /worker/queue/{job_id}`.
- [ ] Implement queue record response schema and route.
- [ ] Verify route tests pass.

### Task 4: Acceptance Evidence and Logs

**Files:**
- Add: `tests/risk/p0_retry_escalation.md`
- Modify: `docs/delivery/ACCEPTANCE_TRACE_MATRIX.md`
- Modify: `docs/changelog/DEVELOPMENT_LOG.md`
- Modify: `docs/delivery/AGENT_FULL_PICTURE.md`

- [ ] Add risk evidence note for `TC-P0-01-02`.
- [ ] Update matrix `AC-P0-01-02` status to `IN_PROGRESS` (or `PASS` if full evidence complete).
- [ ] Append this session in development log.
- [ ] Run full unit tests and capture evidence.

