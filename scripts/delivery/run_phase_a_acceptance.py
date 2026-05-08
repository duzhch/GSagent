#!/usr/bin/env python
"""Run Phase-A unified acceptance checks and emit a single markdown report."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from animal_gs_agent.services.acceptance_runner_service import (
    build_phase_a_markdown_report,
    run_phase_a_checks,
    write_phase_a_markdown_report,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    default_output = repo_root / "tests" / "integration" / "phase_a_unified_acceptance_latest.md"

    parser = argparse.ArgumentParser(description="Phase-A unified acceptance runner")
    parser.add_argument(
        "--workdir",
        default=str(repo_root),
        help="Repository root used as command working directory",
    )
    parser.add_argument(
        "--output",
        default=str(default_output),
        help="Markdown report output path",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    workdir = Path(args.workdir).resolve()
    output = Path(args.output).resolve()

    results = run_phase_a_checks(workdir=workdir)
    report = build_phase_a_markdown_report(results)
    write_phase_a_markdown_report(output, report)

    has_failure = any(item.exit_code != 0 for item in results)
    return 1 if has_failure else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
