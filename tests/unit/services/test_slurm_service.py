from animal_gs_agent.services.slurm_service import poll_slurm_job_state


def test_poll_slurm_job_state_reads_completed_from_sacct(monkeypatch) -> None:
    class _Completed:
        returncode = 0
        stdout = "COMPLETED\n"
        stderr = ""

    monkeypatch.setattr(
        "animal_gs_agent.services.slurm_service.subprocess.run",
        lambda *args, **kwargs: _Completed(),
    )

    state = poll_slurm_job_state("123456")

    assert state == "COMPLETED"


def test_poll_slurm_job_state_falls_back_to_squeue(monkeypatch) -> None:
    calls = {"count": 0}

    class _Fail:
        returncode = 1
        stdout = ""
        stderr = "sacct not ready"

    class _Run:
        returncode = 0
        stdout = "R\n"
        stderr = ""

    def _fake_run(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            return _Fail()
        return _Run()

    monkeypatch.setattr("animal_gs_agent.services.slurm_service.subprocess.run", _fake_run)

    state = poll_slurm_job_state("123456")
    assert state == "RUNNING"
