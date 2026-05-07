"""Slurm queue polling helpers."""

from __future__ import annotations

import subprocess


def _normalize_slurm_state(raw: str) -> str:
    token = raw.strip().split()[0].upper() if raw.strip() else "UNKNOWN"
    if token in {"R", "RUNNING"}:
        return "RUNNING"
    if token in {"PD", "PENDING"}:
        return "PENDING"
    if token.startswith("COMPLETED"):
        return "COMPLETED"
    if token.startswith(
        (
            "FAILED",
            "CANCELLED",
            "TIMEOUT",
            "OUT_OF_MEMORY",
            "NODE_FAIL",
            "PREEMPTED",
            "BOOT_FAIL",
            "DEADLINE",
        )
    ):
        return "FAILED"
    return "UNKNOWN"


def poll_slurm_job_state(submission_id: str) -> str:
    sacct_cmd = [
        "sacct",
        "-j",
        submission_id,
        "--format=State",
        "--noheader",
        "--parsable2",
    ]
    sacct = subprocess.run(sacct_cmd, capture_output=True, text=True, check=False)
    if sacct.returncode == 0:
        for line in sacct.stdout.splitlines():
            value = line.strip().split("|")[0].strip()
            if value:
                return _normalize_slurm_state(value)

    squeue_cmd = ["squeue", "-j", submission_id, "-h", "-o", "%T"]
    squeue = subprocess.run(squeue_cmd, capture_output=True, text=True, check=False)
    if squeue.returncode == 0:
        for line in squeue.stdout.splitlines():
            value = line.strip()
            if value:
                return _normalize_slurm_state(value)

    return "UNKNOWN"
