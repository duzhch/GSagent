#!/usr/bin/env python
"""Simple async worker loop for queued job execution."""

from __future__ import annotations

import argparse
import time

from animal_gs_agent.services.job_service import run_job
from animal_gs_agent.services.run_queue_service import (
    claim_next_run_job,
    mark_run_job_done,
    mark_run_job_failed,
)
from animal_gs_agent.services.workflow_result_service import parse_workflow_outputs
from animal_gs_agent.services.workflow_service import execute_fixed_workflow


def process_one() -> bool:
    job_id = claim_next_run_job()
    if job_id is None:
        return False

    try:
        job = run_job(
            job_id,
            workflow_executor=execute_fixed_workflow,
            workflow_output_parser=parse_workflow_outputs,
        )
        if job is None:
            mark_run_job_failed(job_id, "job_not_found")
            return True
        if job.status == "failed":
            mark_run_job_failed(job_id, job.execution_error or "workflow_failed")
            return True
        if job.status in {"running", "completed"}:
            mark_run_job_done(job_id)
            return True
        mark_run_job_failed(job_id, f"unexpected_status:{job.status}")
        return True
    except Exception as exc:
        mark_run_job_failed(job_id, f"worker_exception:{exc}")
        return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Run async worker loop for queued GS jobs")
    parser.add_argument("--once", action="store_true", help="Process at most one queued job and exit")
    parser.add_argument("--interval-seconds", type=float, default=2.0)
    args = parser.parse_args()

    if args.once:
        process_one()
        return 0

    while True:
        had_job = process_one()
        if not had_job:
            time.sleep(args.interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
