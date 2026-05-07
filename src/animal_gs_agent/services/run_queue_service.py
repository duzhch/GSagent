"""SQLite-backed async run queue."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _queue_db_path() -> Path:
    configured = os.getenv("ANIMAL_GS_AGENT_RUN_QUEUE_SQLITE_PATH")
    if configured and configured.strip():
        return Path(configured)

    job_store_sqlite = os.getenv("ANIMAL_GS_AGENT_JOB_STORE_SQLITE_PATH")
    if job_store_sqlite and job_store_sqlite.strip():
        return Path(job_store_sqlite).with_name("run_queue.db")

    return Path("/tmp/animal_gs_agent_run_queue.db")


def _init_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS run_queue (
                job_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                last_error TEXT
            )
            """
        )
        conn.commit()


def enqueue_run_job(job_id: str) -> str:
    path = _queue_db_path()
    _init_db(path)
    now = _now_iso()
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT status FROM run_queue WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO run_queue(job_id, status, created_at, updated_at, attempts, last_error) VALUES(?, 'pending', ?, ?, 0, NULL)",
                (job_id, now, now),
            )
            conn.commit()
            return "enqueued"
        status = row[0]
        if status in {"pending", "running"}:
            return "already_enqueued"
        conn.execute(
            "UPDATE run_queue SET status='pending', updated_at=?, last_error=NULL WHERE job_id=?",
            (now, job_id),
        )
        conn.commit()
        return "requeued"


def claim_next_run_job() -> str | None:
    path = _queue_db_path()
    _init_db(path)
    now = _now_iso()
    with sqlite3.connect(path) as conn:
        row = conn.execute(
            "SELECT job_id FROM run_queue WHERE status='pending' ORDER BY created_at LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        job_id = row[0]
        updated = conn.execute(
            "UPDATE run_queue SET status='running', updated_at=?, attempts=attempts+1 WHERE job_id=? AND status='pending'",
            (now, job_id),
        )
        conn.commit()
        if updated.rowcount == 0:
            return None
        return job_id


def mark_run_job_done(job_id: str) -> None:
    path = _queue_db_path()
    _init_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE run_queue SET status='done', updated_at=?, last_error=NULL WHERE job_id=?",
            (_now_iso(), job_id),
        )
        conn.commit()


def mark_run_job_failed(job_id: str, error: str) -> None:
    path = _queue_db_path()
    _init_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE run_queue SET status='failed', updated_at=?, last_error=? WHERE job_id=?",
            (_now_iso(), error, job_id),
        )
        conn.commit()


def get_run_queue_record(job_id: str) -> dict | None:
    path = _queue_db_path()
    _init_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute(
            "SELECT job_id, status, created_at, updated_at, attempts, last_error FROM run_queue WHERE job_id = ?",
            (job_id,),
        ).fetchone()
    if row is None:
        return None
    return {
        "job_id": row[0],
        "status": row[1],
        "created_at": row[2],
        "updated_at": row[3],
        "attempts": row[4],
        "last_error": row[5],
    }


def count_pending_jobs() -> int:
    path = _queue_db_path()
    _init_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT COUNT(*) FROM run_queue WHERE status='pending'").fetchone()
    return int(row[0]) if row else 0
