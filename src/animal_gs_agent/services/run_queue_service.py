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


def _max_attempts() -> int:
    raw = os.getenv("ANIMAL_GS_AGENT_RUN_QUEUE_MAX_ATTEMPTS", "3").strip()
    try:
        parsed = int(raw)
    except ValueError:
        return 3
    return max(1, parsed)


def _retry_delay_seconds() -> int:
    raw = os.getenv("ANIMAL_GS_AGENT_RUN_QUEUE_RETRY_DELAY_SECONDS", "10").strip()
    try:
        parsed = int(raw)
    except ValueError:
        return 10
    return max(0, parsed)


def _iso_after_seconds(seconds: int) -> str:
    now = datetime.now(tz=timezone.utc)
    target = now.timestamp() + seconds
    return datetime.fromtimestamp(target, tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _ensure_columns(conn: sqlite3.Connection) -> None:
    existing = {row[1] for row in conn.execute("PRAGMA table_info(run_queue)").fetchall()}
    if "max_attempts" not in existing:
        conn.execute("ALTER TABLE run_queue ADD COLUMN max_attempts INTEGER NOT NULL DEFAULT 3")
    if "next_retry_at" not in existing:
        conn.execute("ALTER TABLE run_queue ADD COLUMN next_retry_at TEXT")
    if "escalated" not in existing:
        conn.execute("ALTER TABLE run_queue ADD COLUMN escalated INTEGER NOT NULL DEFAULT 0")
    if "escalation_reason" not in existing:
        conn.execute("ALTER TABLE run_queue ADD COLUMN escalation_reason TEXT")


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
                last_error TEXT,
                max_attempts INTEGER NOT NULL DEFAULT 3,
                next_retry_at TEXT,
                escalated INTEGER NOT NULL DEFAULT 0,
                escalation_reason TEXT
            )
            """
        )
        _ensure_columns(conn)
        conn.commit()


def enqueue_run_job(job_id: str) -> str:
    path = _queue_db_path()
    _init_db(path)
    now = _now_iso()
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT status FROM run_queue WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            conn.execute(
                """
                INSERT INTO run_queue(
                    job_id, status, created_at, updated_at, attempts, last_error,
                    max_attempts, next_retry_at, escalated, escalation_reason
                ) VALUES(?, 'pending', ?, ?, 0, NULL, ?, NULL, 0, NULL)
                """,
                (job_id, now, now, _max_attempts()),
            )
            conn.commit()
            return "enqueued"
        status = row[0]
        if status in {"pending", "running"}:
            return "already_enqueued"
        conn.execute(
            """
            UPDATE run_queue
            SET status='pending', updated_at=?, last_error=NULL, attempts=0,
                max_attempts=?, next_retry_at=NULL, escalated=0, escalation_reason=NULL
            WHERE job_id=?
            """,
            (now, _max_attempts(), job_id),
        )
        conn.commit()
        return "requeued"


def claim_next_run_job() -> str | None:
    path = _queue_db_path()
    _init_db(path)
    now = _now_iso()
    with sqlite3.connect(path) as conn:
        row = conn.execute(
            """
            SELECT job_id
            FROM run_queue
            WHERE status='pending'
              AND (next_retry_at IS NULL OR next_retry_at <= ?)
            ORDER BY created_at
            LIMIT 1
            """,
            (now,),
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
            "UPDATE run_queue SET status='done', updated_at=?, last_error=NULL, next_retry_at=NULL WHERE job_id=?",
            (_now_iso(), job_id),
        )
        conn.commit()


def mark_run_job_attempt_failure(job_id: str, error: str) -> dict:
    path = _queue_db_path()
    _init_db(path)
    now = _now_iso()
    with sqlite3.connect(path) as conn:
        row = conn.execute(
            "SELECT attempts, max_attempts FROM run_queue WHERE job_id = ?",
            (job_id,),
        ).fetchone()
        if row is None:
            return {
                "queue_status": "missing",
                "attempts": 0,
                "max_attempts": _max_attempts(),
                "escalated": False,
                "next_retry_at": None,
            }

        attempts, max_attempts = int(row[0]), int(row[1])
        if attempts < max_attempts:
            next_retry_at = _iso_after_seconds(_retry_delay_seconds())
            conn.execute(
                """
                UPDATE run_queue
                SET status='pending', updated_at=?, last_error=?, next_retry_at=?,
                    escalated=0, escalation_reason=NULL
                WHERE job_id=?
                """,
                (now, error, next_retry_at, job_id),
            )
            conn.commit()
            return {
                "queue_status": "pending",
                "attempts": attempts,
                "max_attempts": max_attempts,
                "escalated": False,
                "next_retry_at": next_retry_at,
            }

        conn.execute(
            """
            UPDATE run_queue
            SET status='dead', updated_at=?, last_error=?, next_retry_at=NULL,
                escalated=1, escalation_reason='max_attempts_exceeded'
            WHERE job_id=?
            """,
            (now, error, job_id),
        )
        conn.commit()
        return {
            "queue_status": "dead",
            "attempts": attempts,
            "max_attempts": max_attempts,
            "escalated": True,
            "next_retry_at": None,
        }


def mark_run_job_failed(job_id: str, error: str) -> None:
    mark_run_job_attempt_failure(job_id, error)


def get_run_queue_record(job_id: str) -> dict | None:
    path = _queue_db_path()
    _init_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute(
            """
            SELECT job_id, status, created_at, updated_at, attempts, last_error,
                   max_attempts, next_retry_at, escalated, escalation_reason
            FROM run_queue
            WHERE job_id = ?
            """,
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
        "max_attempts": row[6],
        "next_retry_at": row[7],
        "escalated": bool(row[8]),
        "escalation_reason": row[9],
    }


def count_pending_jobs() -> int:
    path = _queue_db_path()
    _init_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT COUNT(*) FROM run_queue WHERE status='pending'").fetchone()
    return int(row[0]) if row else 0


def count_dead_jobs() -> int:
    path = _queue_db_path()
    _init_db(path)
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT COUNT(*) FROM run_queue WHERE status='dead'").fetchone()
    return int(row[0]) if row else 0
