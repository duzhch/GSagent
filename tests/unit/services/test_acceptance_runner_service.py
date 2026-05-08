from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys

from animal_gs_agent.services.acceptance_runner_service import (
    AcceptanceCheck,
    build_phase_a_markdown_report,
    get_phase_a_checks,
    run_phase_a_checks,
    write_phase_a_markdown_report,
)


def test_get_phase_a_checks_covers_expected_ac_ids() -> None:
    checks = get_phase_a_checks()
    ac_ids = {check.ac_id for check in checks}

    assert len(checks) >= 5
    assert "AC-P0-01-01" in ac_ids
    assert "AC-P0-01-02" in ac_ids
    assert "AC-P0-01-03" in ac_ids
    assert "AC-P1-04-01" in ac_ids
    assert "AC-P1-04-02" in ac_ids
    assert all(check.command[0] == sys.executable for check in checks)
    assert all(check.command[1:3] == ["-m", "pytest"] for check in checks)


def test_run_phase_a_checks_collects_runner_outcomes(tmp_path: Path) -> None:
    checks = [
        AcceptanceCheck(
            check_id="C1",
            feature_id="F-P0-01-01",
            story_id="S-P0-01-02",
            ac_id="AC-P0-01-02",
            name="dummy-pass",
            command=["python", "-m", "pytest", "tests/unit/p0_trace_schema_test.py", "-q"],
            evidence_path_hint="tests/risk/p0_retry_escalation.md",
        ),
        AcceptanceCheck(
            check_id="C2",
            feature_id="F-P1-04-01",
            story_id="S-P1-04-01",
            ac_id="AC-P1-04-01",
            name="dummy-fail",
            command=["python", "-m", "pytest", "tests/unit/api/test_job_escalation.py", "-q"],
            evidence_path_hint="tests/risk/p1_approval_gate.md",
        ),
    ]

    def fake_runner(command: list[str], cwd: Path) -> SimpleNamespace:
        joined = " ".join(command)
        if "test_job_escalation.py" in joined:
            return SimpleNamespace(returncode=1, stdout="bad", stderr="boom")
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    results = run_phase_a_checks(checks, workdir=tmp_path, runner=fake_runner)

    assert len(results) == 2
    assert results[0].exit_code == 0
    assert results[1].exit_code == 1
    assert results[0].workdir == str(tmp_path)


def test_report_render_and_write(tmp_path: Path) -> None:
    check = AcceptanceCheck(
        check_id="C1",
        feature_id="F-P0-01-01",
        story_id="S-P0-01-02",
        ac_id="AC-P0-01-02",
        name="dummy-pass",
        command=["python", "-m", "pytest", "tests/unit/p0_trace_schema_test.py", "-q"],
        evidence_path_hint="tests/risk/p0_retry_escalation.md",
    )
    results = run_phase_a_checks(
        [check],
        workdir=tmp_path,
        runner=lambda command, cwd: SimpleNamespace(returncode=0, stdout="ok", stderr=""),
    )

    report = build_phase_a_markdown_report(results)
    output_path = tmp_path / "reports" / "phase_a.md"
    written_path = write_phase_a_markdown_report(output_path, report)

    assert "Phase A Unified Acceptance Report" in report
    assert "AC-P0-01-02" in report
    assert "PASS" in report
    assert written_path == output_path
    assert output_path.exists()
