from animal_gs_agent.services.run_queue_service import (
    claim_next_run_job,
    enqueue_run_job,
    get_run_queue_record,
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
