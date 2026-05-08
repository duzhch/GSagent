"""Phase-A unified acceptance runner service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import time
from typing import Callable, Protocol


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass(frozen=True)
class AcceptanceCheck:
    check_id: str
    feature_id: str
    story_id: str
    ac_id: str
    name: str
    command: list[str]
    evidence_path_hint: str


@dataclass(frozen=True)
class AcceptanceCheckResult:
    check: AcceptanceCheck
    exit_code: int
    stdout: str
    stderr: str
    workdir: str
    started_at: str
    finished_at: str
    duration_seconds: float

    @property
    def status(self) -> str:
        return "PASS" if self.exit_code == 0 else "FAIL"


class CommandResult(Protocol):
    returncode: int
    stdout: str
    stderr: str


CommandRunner = Callable[[list[str], Path], CommandResult]


def _default_runner(command: list[str], cwd: Path) -> CommandResult:
    return subprocess.run(
        command,
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
    )


def get_phase_a_checks() -> list[AcceptanceCheck]:
    python_cmd = sys.executable
    return [
        AcceptanceCheck(
            check_id="P0-SUPERVISOR-FLOW",
            feature_id="F-P0-01-01",
            story_id="S-P0-01-02",
            ac_id="AC-P0-01-01",
            name="supervisor flow integration",
            command=[python_cmd, "-m", "pytest", "tests/unit/services/test_worker_service.py", "-q"],
            evidence_path_hint="tests/integration/p0_supervisor_flow.md",
        ),
        AcceptanceCheck(
            check_id="P0-RETRY-ESCALATION",
            feature_id="F-P0-01-01",
            story_id="S-P0-01-02",
            ac_id="AC-P0-01-02",
            name="retry budget escalation risk",
            command=[python_cmd, "-m", "pytest", "tests/unit/services/test_worker_service.py", "-q"],
            evidence_path_hint="tests/risk/p0_retry_escalation.md",
        ),
        AcceptanceCheck(
            check_id="P0-TRACE-VISIBILITY",
            feature_id="F-P0-01-01",
            story_id="S-P0-01-04",
            ac_id="AC-P0-01-03",
            name="trace visibility e2e readiness",
            command=[python_cmd, "-m", "pytest", "tests/unit/api/test_job_trace.py", "-q"],
            evidence_path_hint="tests/e2e/p0_trace_visibility.md",
        ),
        AcceptanceCheck(
            check_id="P1-APPROVAL-GATE",
            feature_id="F-P1-04-01",
            story_id="S-P1-04-01",
            ac_id="AC-P1-04-01",
            name="approval gate risk",
            command=[python_cmd, "-m", "pytest", "tests/unit/api/test_job_escalation.py", "-q"],
            evidence_path_hint="tests/risk/p1_approval_gate.md",
        ),
        AcceptanceCheck(
            check_id="P1-OVERRIDE-LOG",
            feature_id="F-P1-04-02",
            story_id="S-P1-04-02",
            ac_id="AC-P1-04-02",
            name="override audit log integration",
            command=[python_cmd, "-m", "pytest", "tests/unit/api/test_job_escalation.py", "-q"],
            evidence_path_hint="tests/integration/p1_override_log.md",
        ),
    ]


def run_phase_a_checks(
    checks: list[AcceptanceCheck] | None = None,
    *,
    workdir: Path,
    runner: CommandRunner | None = None,
) -> list[AcceptanceCheckResult]:
    active_checks = checks if checks is not None else get_phase_a_checks()
    command_runner = runner or _default_runner

    results: list[AcceptanceCheckResult] = []
    for check in active_checks:
        started = _utc_now()
        begin = time.perf_counter()
        output = command_runner(check.command, workdir)
        duration = time.perf_counter() - begin
        finished = _utc_now()
        results.append(
            AcceptanceCheckResult(
                check=check,
                exit_code=int(output.returncode),
                stdout=output.stdout or "",
                stderr=output.stderr or "",
                workdir=str(workdir),
                started_at=started,
                finished_at=finished,
                duration_seconds=duration,
            )
        )
    return results


def build_phase_a_markdown_report(results: list[AcceptanceCheckResult]) -> str:
    passed = sum(1 for item in results if item.exit_code == 0)
    total = len(results)
    failed = total - passed
    lines = [
        "# Phase A Unified Acceptance Report",
        "",
        f"- Generated at: {_utc_now()}",
        f"- Total checks: {total}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        "",
        "| Check ID | AC ID | Feature ID | Story ID | Status | Duration(s) | Evidence Hint |",
        "|---|---|---|---|---|---:|---|",
    ]
    for item in results:
        lines.append(
            f"| `{item.check.check_id}` | `{item.check.ac_id}` | `{item.check.feature_id}` | "
            f"`{item.check.story_id}` | {item.status} | {item.duration_seconds:.2f} | "
            f"`{item.check.evidence_path_hint}` |"
        )
    return "\n".join(lines) + "\n"


def write_phase_a_markdown_report(output_path: Path, report_content: str) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_content, encoding="utf-8")
    return output_path
