from animal_gs_agent.schemas.dataset_profile import DatasetPathChecks, DatasetProfile
from animal_gs_agent.schemas.jobs import JobSubmissionRequest
from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult
from animal_gs_agent.services.job_service import create_job, jobs_store
from animal_gs_agent.services.run_queue_service import enqueue_run_job, get_run_queue_record
from animal_gs_agent.services.worker_service import get_worker_health_snapshot, process_next_queued_job


def _request() -> JobSubmissionRequest:
    return JobSubmissionRequest(
        user_message="Run genomic selection for daily_gain",
        trait_name="daily_gain",
        phenotype_path="/tmp/pheno.csv",
        genotype_path="/tmp/geno.vcf",
    )


def _task() -> TaskUnderstandingResult:
    return TaskUnderstandingResult(
        request_scope="supported_gs",
        trait_name="daily_gain",
        user_goal="rank candidates",
        candidate_fixed_effects=["sex"],
        population_description="pig",
        missing_inputs=[],
        confidence=0.9,
        clarification_needed=False,
    )


def _profile() -> DatasetProfile:
    return DatasetProfile(
        phenotype_path="/tmp/pheno.csv",
        genotype_path="/tmp/geno.vcf",
        path_checks=DatasetPathChecks(phenotype_exists=True, genotype_exists=True),
        phenotype_format="csv",
        genotype_format="vcf",
        phenotype_headers=["animal_id", "daily_gain"],
        trait_column_present=True,
        validation_flags=[],
    )


def test_worker_health_snapshot_reports_pending_jobs(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ANIMAL_GS_AGENT_RUN_QUEUE_SQLITE_PATH", str(tmp_path / "queue.db"))
    monkeypatch.setenv("ANIMAL_GS_AGENT_ASYNC_RUN_ENABLED", "1")

    snapshot = get_worker_health_snapshot()

    assert snapshot.async_run_enabled is True
    assert snapshot.pending_jobs == 0


def test_process_next_queued_job_consumes_pending_job(monkeypatch, tmp_path) -> None:
    queue_db = tmp_path / "queue.db"
    store_db = tmp_path / "jobs.db"
    monkeypatch.setenv("ANIMAL_GS_AGENT_RUN_QUEUE_SQLITE_PATH", str(queue_db))
    monkeypatch.setenv("ANIMAL_GS_AGENT_JOB_STORE_SQLITE_PATH", str(store_db))
    jobs_store.clear()

    created = create_job(_request(), task_understanding=_task(), dataset_profile=_profile())
    enqueue_run_job(created.job_id)

    monkeypatch.setattr(
        "animal_gs_agent.services.worker_service.execute_fixed_workflow",
        lambda job: type(
            "ExecutionResult",
            (),
            {
                "backend": "native_nextflow",
                "command": ["nextflow", "run", "main.nf"],
                "result_dir": f"/tmp/{job.job_id}",
                "status": "completed",
                "submission_id": None,
            },
        )(),
    )
    monkeypatch.setattr(
        "animal_gs_agent.services.worker_service.parse_workflow_outputs",
        lambda result_dir, trait_name, top_n=10: None,
    )

    outcome = process_next_queued_job()

    assert outcome.processed is True
    assert outcome.job_id == created.job_id
    assert outcome.job_status == "completed"
    assert outcome.queue_status == "done"


def test_process_next_queued_job_escalates_after_retry_budget(monkeypatch, tmp_path) -> None:
    queue_db = tmp_path / "queue.db"
    store_db = tmp_path / "jobs.db"
    monkeypatch.setenv("ANIMAL_GS_AGENT_RUN_QUEUE_SQLITE_PATH", str(queue_db))
    monkeypatch.setenv("ANIMAL_GS_AGENT_JOB_STORE_SQLITE_PATH", str(store_db))
    monkeypatch.setenv("ANIMAL_GS_AGENT_RUN_QUEUE_MAX_ATTEMPTS", "1")
    monkeypatch.setenv("ANIMAL_GS_AGENT_RUN_QUEUE_RETRY_DELAY_SECONDS", "0")
    jobs_store.clear()

    created = create_job(_request(), task_understanding=_task(), dataset_profile=_profile())
    enqueue_run_job(created.job_id)

    monkeypatch.setattr(
        "animal_gs_agent.services.worker_service.execute_fixed_workflow",
        lambda job: (_ for _ in ()).throw(RuntimeError("workflow boom")),
    )

    outcome = process_next_queued_job()
    assert outcome.processed is True
    assert outcome.job_id == created.job_id
    assert outcome.queue_status == "dead"
    assert outcome.escalated is True

    record = get_run_queue_record(created.job_id)
    assert record is not None
    assert record["status"] == "dead"
    assert record["escalated"] is True
