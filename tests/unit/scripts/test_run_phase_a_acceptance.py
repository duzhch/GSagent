from __future__ import annotations

import importlib.util
from pathlib import Path

from animal_gs_agent.services.acceptance_runner_service import AcceptanceCheck, AcceptanceCheckResult


def _load_script_module():
    script_path = (
        Path(__file__).resolve().parents[3] / "scripts" / "delivery" / "run_phase_a_acceptance.py"
    )
    spec = importlib.util.spec_from_file_location("run_phase_a_acceptance", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_writes_report_file(monkeypatch, tmp_path: Path) -> None:
    module = _load_script_module()
    report_path = tmp_path / "phase_a.md"

    check = AcceptanceCheck(
        check_id="C1",
        feature_id="F-P0-01-01",
        story_id="S-P0-01-02",
        ac_id="AC-P0-01-02",
        name="dummy",
        command=["python", "-m", "pytest", "tests/unit/p0_trace_schema_test.py", "-q"],
        evidence_path_hint="tests/risk/p0_retry_escalation.md",
    )
    result = AcceptanceCheckResult(
        check=check,
        exit_code=0,
        stdout="ok",
        stderr="",
        workdir=str(tmp_path),
        started_at="2026-05-08T00:00:00Z",
        finished_at="2026-05-08T00:00:01Z",
        duration_seconds=1.0,
    )

    monkeypatch.setattr(module, "run_phase_a_checks", lambda **kwargs: [result])
    exit_code = module.main(["--workdir", str(tmp_path), "--output", str(report_path)])

    assert exit_code == 0
    assert report_path.exists()
    assert "Phase A Unified Acceptance Report" in report_path.read_text(encoding="utf-8")


def test_cli_returns_nonzero_when_any_check_fails(monkeypatch, tmp_path: Path) -> None:
    module = _load_script_module()
    report_path = tmp_path / "phase_a.md"

    check = AcceptanceCheck(
        check_id="C1",
        feature_id="F-P0-01-01",
        story_id="S-P0-01-02",
        ac_id="AC-P0-01-02",
        name="dummy",
        command=["python", "-m", "pytest", "tests/unit/p0_trace_schema_test.py", "-q"],
        evidence_path_hint="tests/risk/p0_retry_escalation.md",
    )
    result = AcceptanceCheckResult(
        check=check,
        exit_code=1,
        stdout="bad",
        stderr="boom",
        workdir=str(tmp_path),
        started_at="2026-05-08T00:00:00Z",
        finished_at="2026-05-08T00:00:01Z",
        duration_seconds=1.0,
    )

    monkeypatch.setattr(module, "run_phase_a_checks", lambda **kwargs: [result])
    exit_code = module.main(["--workdir", str(tmp_path), "--output", str(report_path)])

    assert exit_code == 1
