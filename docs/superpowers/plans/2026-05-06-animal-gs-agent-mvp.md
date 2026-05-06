# Animal GS Agent MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a maintainable MVP repository for an animal breeding genomic selection agent with a LangGraph orchestration layer and a fixed one-stage GBLUP workflow.

**Architecture:** The repository will separate the API layer, agent graph, worker execution contracts, and packaging artifacts. The first implementation pass will establish typed boundaries, persistent job metadata, and a traceable execution path before integrating full PLINK2 and BLUPF90+ execution.

**Tech Stack:** Python 3.11, FastAPI, LangGraph, Pydantic, Celery, Redis, PostgreSQL, pytest, Docker Compose, Next.js, PLINK 2, BLUPF90+, R

---

### Task 1: Initialize Repository Standards

**Files:**
- Create: `README.md`
- Create: `.gitignore`
- Create: `docs/changelog/CHANGELOG.md`
- Create: `docs/changelog/DEVELOPMENT_LOG.md`
- Create: `docs/adr/ADR-0001-stack-and-workflow.md`
- Test: repository file presence check

- [ ] **Step 1: Verify repository starts without project metadata files**

Run: `find . -maxdepth 2 \\( -name README.md -o -name .gitignore -o -name CHANGELOG.md \\) | sort`
Expected: no repository-level files listed for the new project before initialization

- [ ] **Step 2: Create the repository metadata files**

```text
README.md documents the MVP purpose and repository conventions.
.gitignore excludes local environments, outputs, and raw runtime artifacts.
CHANGELOG.md and DEVELOPMENT_LOG.md establish maintenance records.
ADR-0001 captures the architecture decision for LangGraph plus one-stage GBLUP.
```

- [ ] **Step 3: Verify metadata files exist**

Run: `find . -maxdepth 3 \\( -name README.md -o -name .gitignore -o -name CHANGELOG.md -o -name DEVELOPMENT_LOG.md -o -name 'ADR-0001-*' \\) | sort`
Expected: all five files are listed inside the repository

- [ ] **Step 4: Commit**

```bash
git add README.md .gitignore docs/changelog/CHANGELOG.md docs/changelog/DEVELOPMENT_LOG.md docs/adr/ADR-0001-stack-and-workflow.md
git commit -m "chore: initialize repository documentation"
```

### Task 2: Create the Python Service Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `src/animal_gs_agent/config.py`
- Create: `src/animal_gs_agent/api/app.py`
- Create: `src/animal_gs_agent/api/routes/health.py`
- Create: `tests/unit/api/test_health.py`
- Test: `tests/unit/api/test_health.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient

from animal_gs_agent.api.app import create_app


def test_healthcheck_returns_service_identity() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "animal-gs-agent",
        "status": "ok",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/api/test_health.py -v`
Expected: FAIL because `animal_gs_agent.api.app` does not exist yet

- [ ] **Step 3: Write minimal implementation**

```python
from fastapi import APIRouter, FastAPI


def create_health_router() -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"service": "animal-gs-agent", "status": "ok"}

    return router


def create_app() -> FastAPI:
    app = FastAPI(title="Animal GS Agent")
    app.include_router(create_health_router())
    return app
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/api/test_health.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/animal_gs_agent/config.py src/animal_gs_agent/api/app.py src/animal_gs_agent/api/routes/health.py tests/unit/api/test_health.py
git commit -m "feat: add api service skeleton"
```

### Task 3: Create the LangGraph Intake Contract

**Files:**
- Create: `src/animal_gs_agent/agent/state.py`
- Create: `src/animal_gs_agent/agent/graph.py`
- Create: `tests/unit/agent/test_request_scope.py`
- Test: `tests/unit/agent/test_request_scope.py`

- [ ] **Step 1: Write the failing test**

```python
from animal_gs_agent.agent.graph import classify_request
from animal_gs_agent.agent.state import IntakeState


def test_classify_request_marks_gs_request_as_supported() -> None:
    state = IntakeState(user_message="Please run genomic selection for trait milk_yield")

    updated = classify_request(state)

    assert updated["request_scope"] == "supported_gs"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/agent/test_request_scope.py -v`
Expected: FAIL because the agent modules do not exist yet

- [ ] **Step 3: Write minimal implementation**

```python
from typing import Literal, TypedDict


class IntakeState(TypedDict, total=False):
    user_message: str
    request_scope: Literal["supported_gs", "unsupported"]


def classify_request(state: IntakeState) -> IntakeState:
    message = state["user_message"].lower()
    if "genomic selection" in message or "gs" in message:
        return {**state, "request_scope": "supported_gs"}
    return {**state, "request_scope": "unsupported"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/agent/test_request_scope.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/animal_gs_agent/agent/state.py src/animal_gs_agent/agent/graph.py tests/unit/agent/test_request_scope.py
git commit -m "feat: add langgraph intake contract"
```

### Task 4: Create the Job Submission Contract

**Files:**
- Create: `src/animal_gs_agent/api/routes/jobs.py`
- Create: `src/animal_gs_agent/schemas/jobs.py`
- Create: `src/animal_gs_agent/services/job_service.py`
- Create: `tests/unit/api/test_job_submission.py`
- Test: `tests/unit/api/test_job_submission.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient

from animal_gs_agent.api.app import create_app


def test_submit_job_returns_pending_job() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/jobs",
        json={
            "user_message": "Run genomic selection for daily_gain",
            "trait_name": "daily_gain",
            "phenotype_path": "data/demo/phenotypes.csv",
            "genotype_path": "data/demo/genotypes.pgen",
        },
    )

    body = response.json()

    assert response.status_code == 202
    assert body["status"] == "pending"
    assert body["trait_name"] == "daily_gain"
    assert "job_id" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/api/test_job_submission.py -v`
Expected: FAIL because `/jobs` is not implemented

- [ ] **Step 3: Write minimal implementation**

```python
from uuid import uuid4


def create_job(payload: dict[str, str]) -> dict[str, str]:
    return {
        "job_id": uuid4().hex[:8],
        "status": "pending",
        "trait_name": payload["trait_name"],
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/api/test_job_submission.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/animal_gs_agent/api/routes/jobs.py src/animal_gs_agent/schemas/jobs.py src/animal_gs_agent/services/job_service.py tests/unit/api/test_job_submission.py
git commit -m "feat: add job submission contract"
```

### Task 5: Create Packaging and Local Startup Scaffolding

**Files:**
- Create: `docker-compose.yml`
- Create: `Dockerfile.api`
- Create: `Dockerfile.worker`
- Create: `.env.example`
- Create: `tests/smoke/test_repository_layout.py`
- Test: `tests/smoke/test_repository_layout.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path


def test_packaging_files_exist() -> None:
    assert Path("docker-compose.yml").exists()
    assert Path("Dockerfile.api").exists()
    assert Path("Dockerfile.worker").exists()
    assert Path(".env.example").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/smoke/test_repository_layout.py -v`
Expected: FAIL because the packaging files do not exist yet

- [ ] **Step 3: Write minimal implementation**

```yaml
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/smoke/test_repository_layout.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml Dockerfile.api Dockerfile.worker .env.example tests/smoke/test_repository_layout.py
git commit -m "chore: add packaging scaffold"
```

