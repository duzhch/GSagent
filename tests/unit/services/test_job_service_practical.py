import sqlite3

from animal_gs_agent.schemas.dataset_profile import DatasetPathChecks, DatasetProfile
from animal_gs_agent.schemas.jobs import JobSubmissionRequest
from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult
from animal_gs_agent.services.job_service import create_job, get_job, jobs_store, refresh_running_job, run_job
from animal_gs_agent.services.workflow_service import WorkflowExecutionResult


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


def test_job_store_persists_and_recovers_from_disk(monkeypatch, tmp_path) -> None:
    store_file = tmp_path / "jobs_store.json"
    monkeypatch.setenv("ANIMAL_GS_AGENT_JOB_STORE_PATH", str(store_file))
    jobs_store.clear()

    created = create_job(_request(), task_understanding=_task(), dataset_profile=_profile())
    job_id = created.job_id
    assert store_file.exists() is True

    jobs_store.clear()
    recovered = get_job(job_id)
    assert recovered is not None
    assert recovered.job_id == job_id
    assert recovered.trait_name == "daily_gain"


def test_run_job_is_idempotent_when_job_already_completed(monkeypatch) -> None:
    monkeypatch.delenv("ANIMAL_GS_AGENT_JOB_STORE_PATH", raising=False)
    jobs_store.clear()

    created = create_job(_request(), task_understanding=_task(), dataset_profile=_profile())
    job_id = created.job_id

    calls = {"n": 0}

    def fake_executor(job):
        calls["n"] += 1
        return WorkflowExecutionResult(
            backend="native_nextflow",
            command=["nextflow", "run", "main.nf"],
            result_dir=f"/tmp/{job.job_id}",
            status="completed",
        )

    first = run_job(job_id, workflow_executor=fake_executor)
    second = run_job(job_id, workflow_executor=fake_executor)

    assert first is not None
    assert second is not None
    assert first.status == "completed"
    assert second.status == "completed"
    assert calls["n"] == 1


def test_job_store_persists_and_recovers_from_sqlite(monkeypatch, tmp_path) -> None:
    sqlite_path = tmp_path / "jobs_store.db"
    monkeypatch.setenv("ANIMAL_GS_AGENT_JOB_STORE_SQLITE_PATH", str(sqlite_path))
    monkeypatch.delenv("ANIMAL_GS_AGENT_JOB_STORE_PATH", raising=False)
    jobs_store.clear()

    created = create_job(_request(), task_understanding=_task(), dataset_profile=_profile())
    job_id = created.job_id
    assert sqlite_path.exists() is True

    jobs_store.clear()
    recovered = get_job(job_id)
    assert recovered is not None
    assert recovered.job_id == job_id
    assert recovered.trait_name == "daily_gain"


def test_refresh_running_job_loads_store_before_lookup(monkeypatch, tmp_path) -> None:
    sqlite_path = tmp_path / "jobs_store.db"
    monkeypatch.setenv("ANIMAL_GS_AGENT_JOB_STORE_SQLITE_PATH", str(sqlite_path))
    monkeypatch.delenv("ANIMAL_GS_AGENT_JOB_STORE_PATH", raising=False)
    jobs_store.clear()

    created = create_job(_request(), task_understanding=_task(), dataset_profile=_profile())
    job_id = created.job_id

    jobs_store.clear()
    refreshed = refresh_running_job(job_id)
    assert refreshed is not None
    assert refreshed.job_id == job_id


def test_get_job_reloads_sqlite_when_in_memory_copy_is_stale(monkeypatch, tmp_path) -> None:
    sqlite_path = tmp_path / "jobs_store.db"
    monkeypatch.setenv("ANIMAL_GS_AGENT_JOB_STORE_SQLITE_PATH", str(sqlite_path))
    monkeypatch.delenv("ANIMAL_GS_AGENT_JOB_STORE_PATH", raising=False)
    jobs_store.clear()

    created = create_job(_request(), task_understanding=_task(), dataset_profile=_profile())
    job_id = created.job_id
    stale = get_job(job_id)
    assert stale is not None
    assert stale.status == "queued"

    external_completed = stale.model_copy(update={"status": "completed"})
    with sqlite3.connect(sqlite_path) as conn:
        conn.execute(
            "UPDATE jobs SET payload = ? WHERE job_id = ?",
            (external_completed.model_dump_json(), job_id),
        )
        conn.commit()

    refreshed = get_job(job_id)
    assert refreshed is not None
    assert refreshed.status == "completed"


def test_create_job_attaches_validation_protocol_plan() -> None:
    created = create_job(_request(), task_understanding=_task(), dataset_profile=_profile())

    assert created.validation_protocol_plan is not None
    protocols = {item.scenario_id: item for item in created.validation_protocol_plan.protocols}

    assert set(protocols) == {"within_pop", "cross_pop"}

    within = protocols["within_pop"]
    assert within.metrics == ["within_pop_pearson", "within_pop_rmse"]
    assert within.split_records[0].train_population == "pig"
    assert within.split_records[0].validation_population == "pig"

    cross = protocols["cross_pop"]
    assert cross.metrics == ["cross_pop_pearson", "cross_pop_rmse"]
    assert cross.split_records[0].train_population == "pig"
    assert cross.split_records[0].validation_population == "held-out population"
