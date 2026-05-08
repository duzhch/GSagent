from animal_gs_agent.services.run_queue_service import (
    claim_next_run_job,
    enqueue_run_job,
    get_run_queue_record,
    mark_run_job_attempt_failure,
)


def test_enqueue_and_claim_run_job(monkeypatch, tmp_path) -> None:
    queue_db = tmp_path / "run_queue.db"
    monkeypatch.setenv("ANIMAL_GS_AGENT_RUN_QUEUE_SQLITE_PATH", str(queue_db))

    status = enqueue_run_job("job001")
    assert status == "enqueued"

    claimed = claim_next_run_job()
    assert claimed == "job001"

    record = get_run_queue_record("job001")
    assert record is not None
    assert record["status"] == "running"


def test_enqueue_same_job_twice_returns_already_enqueued(monkeypatch, tmp_path) -> None:
    queue_db = tmp_path / "run_queue.db"
    monkeypatch.setenv("ANIMAL_GS_AGENT_RUN_QUEUE_SQLITE_PATH", str(queue_db))

    first = enqueue_run_job("job001")
    second = enqueue_run_job("job001")

    assert first == "enqueued"
    assert second == "already_enqueued"


def test_failed_attempt_under_budget_is_requeued(monkeypatch, tmp_path) -> None:
    queue_db = tmp_path / "run_queue.db"
    monkeypatch.setenv("ANIMAL_GS_AGENT_RUN_QUEUE_SQLITE_PATH", str(queue_db))
    monkeypatch.setenv("ANIMAL_GS_AGENT_RUN_QUEUE_MAX_ATTEMPTS", "3")

    enqueue_run_job("job001")
    claimed = claim_next_run_job()
    assert claimed == "job001"

    outcome = mark_run_job_attempt_failure("job001", "workflow_runtime_error")
    assert outcome["queue_status"] == "pending"
    assert outcome["escalated"] is False

    record = get_run_queue_record("job001")
    assert record is not None
    assert record["status"] == "pending"
    assert record["attempts"] == 1


def test_failed_attempt_over_budget_becomes_dead_and_escalated(monkeypatch, tmp_path) -> None:
    queue_db = tmp_path / "run_queue.db"
    monkeypatch.setenv("ANIMAL_GS_AGENT_RUN_QUEUE_SQLITE_PATH", str(queue_db))
    monkeypatch.setenv("ANIMAL_GS_AGENT_RUN_QUEUE_MAX_ATTEMPTS", "1")

    enqueue_run_job("job001")
    claimed = claim_next_run_job()
    assert claimed == "job001"

    outcome = mark_run_job_attempt_failure("job001", "workflow_runtime_error")
    assert outcome["queue_status"] == "dead"
    assert outcome["escalated"] is True

    record = get_run_queue_record("job001")
    assert record is not None
    assert record["status"] == "dead"
    assert record["escalated"] is True
    assert record["escalation_reason"] == "max_attempts_exceeded"
