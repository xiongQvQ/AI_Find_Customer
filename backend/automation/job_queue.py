"""Persistent queue for headless hunt jobs."""

from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any


_DDL = """
CREATE TABLE IF NOT EXISTS hunt_jobs (
  id TEXT PRIMARY KEY,
  payload_json TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',
  available_at TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  started_at TEXT DEFAULT '',
  finished_at TEXT DEFAULT '',
  claimed_by TEXT DEFAULT '',
  attempt_count INTEGER NOT NULL DEFAULT 0,
  last_error TEXT DEFAULT '',
  last_hunt_id TEXT DEFAULT '',
  progress_stage TEXT DEFAULT '',
  progress_message TEXT DEFAULT '',
  template_seed_status TEXT DEFAULT '',
  template_seed_source TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_hunt_jobs_status_available
ON hunt_jobs(status, available_at, created_at);
"""


class HuntJobQueue:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(_DDL)
            self._ensure_column(conn, "hunt_jobs", "progress_stage", "TEXT DEFAULT ''")
            self._ensure_column(conn, "hunt_jobs", "progress_message", "TEXT DEFAULT ''")
            self._ensure_column(conn, "hunt_jobs", "template_seed_status", "TEXT DEFAULT ''")
            self._ensure_column(conn, "hunt_jobs", "template_seed_source", "TEXT DEFAULT ''")

    def _ensure_column(self, conn: sqlite3.Connection, table_name: str, column_name: str, definition: str) -> None:
        columns = {
            row["name"]
            for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        }
        if column_name not in columns:
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")

    def enqueue(self, payload: dict[str, Any], *, now_iso: str, available_at: str | None = None) -> str:
        job_id = str(uuid.uuid4())
        template_seed = payload.get("template_seed") if isinstance(payload.get("template_seed"), dict) else None
        template_seed_status = "ready" if template_seed else "pending"
        template_seed_source = str((template_seed or {}).get("source", "") or "")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO hunt_jobs (
                  id, payload_json, status, available_at, created_at, updated_at,
                  progress_stage, progress_message, template_seed_status, template_seed_source
                ) VALUES (?, ?, 'queued', ?, ?, ?, 'queued', 'Waiting for consumer to claim', ?, ?)
                """,
                (
                    job_id,
                    json.dumps(payload, ensure_ascii=False),
                    available_at or now_iso,
                    now_iso,
                    now_iso,
                    template_seed_status,
                    template_seed_source,
                ),
            )
        return job_id

    def count_by_status(self, *statuses: str) -> int:
        if not statuses:
            return 0
        placeholders = ", ".join("?" for _ in statuses)
        with self._connect() as conn:
            row = conn.execute(
                f"SELECT COUNT(*) FROM hunt_jobs WHERE status IN ({placeholders})",
                list(statuses),
            ).fetchone()
        return int(row[0]) if row else 0

    def count_finished_since(self, status: str, since_iso: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM hunt_jobs WHERE status = ? AND finished_at >= ?",
                (status, since_iso),
            ).fetchone()
        return int(row[0]) if row else 0

    def count_retrying_since(self, since_iso: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) FROM hunt_jobs
                WHERE status IN ('queued', 'running')
                  AND last_error != ''
                  AND updated_at >= ?
                """,
                (since_iso,),
            ).fetchone()
        return int(row[0]) if row else 0

    def list_recent_retrying_jobs(self, *, since_iso: str, limit: int = 5) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM hunt_jobs
                WHERE status IN ('queued', 'running')
                  AND last_error != ''
                  AND updated_at >= ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (since_iso, max(1, int(limit))),
            ).fetchall()
        results: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            try:
                item["payload"] = json.loads(str(item.get("payload_json") or "{}"))
            except json.JSONDecodeError:
                item["payload"] = {}
            results.append(item)
        return results

    def claim_next(self, *, worker_id: str, now_iso: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            conn.isolation_level = None
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                """
                SELECT * FROM hunt_jobs
                WHERE status = 'queued'
                  AND available_at <= ?
                  AND COALESCE(template_seed_status, '') != 'preparing'
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (now_iso,),
            ).fetchone()
            if not row:
                conn.execute("COMMIT")
                return None
            conn.execute(
                """
                UPDATE hunt_jobs
                SET status = 'running',
                    claimed_by = ?,
                    started_at = ?,
                    updated_at = ?,
                    attempt_count = attempt_count + 1
                WHERE id = ?
                """,
                (worker_id, now_iso, now_iso, row["id"]),
            )
            conn.execute("COMMIT")
        return self.get(str(row["id"]))

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM hunt_jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            return None
        data = dict(row)
        try:
            data["payload"] = json.loads(str(data.get("payload_json") or "{}"))
        except json.JSONDecodeError:
            data["payload"] = {}
        return data

    def is_cancellation_requested(self, job_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT status, progress_stage FROM hunt_jobs WHERE id = ?",
                (job_id,),
            ).fetchone()
        if not row:
            return False
        status = str(row["status"] or "")
        progress_stage = str(row["progress_stage"] or "")
        return status == "failed" and progress_stage == "cancelled"

    def get_by_hunt_id(self, hunt_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM hunt_jobs
                WHERE last_hunt_id = ?
                ORDER BY updated_at DESC, created_at DESC
                LIMIT 1
                """,
                (hunt_id,),
            ).fetchone()
        if not row:
            return None
        data = dict(row)
        try:
            data["payload"] = json.loads(str(data.get("payload_json") or "{}"))
        except json.JSONDecodeError:
            data["payload"] = {}
        return data

    def list_jobs(self, *, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM hunt_jobs
                ORDER BY
                  CASE status
                    WHEN 'running' THEN 0
                    WHEN 'queued' THEN 1
                    WHEN 'failed' THEN 2
                    WHEN 'completed' THEN 3
                    ELSE 4
                  END,
                  updated_at DESC,
                  created_at DESC
                LIMIT ?
                """,
                (max(1, int(limit)),),
            ).fetchall()
        results: list[dict[str, Any]] = []
        for row in rows:
            data = dict(row)
            try:
                data["payload"] = json.loads(str(data.get("payload_json") or "{}"))
            except json.JSONDecodeError:
                data["payload"] = {}
            results.append(data)
        return results

    def mark_completed(self, job_id: str, *, hunt_id: str, finished_at: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE hunt_jobs
                SET status = 'completed',
                    finished_at = ?,
                    updated_at = ?,
                    last_hunt_id = ?,
                    last_error = '',
                    progress_stage = 'completed',
                    progress_message = 'Queue job completed successfully'
                WHERE id = ?
                """,
                (finished_at, finished_at, hunt_id, job_id),
            )

    def mark_failed(self, job_id: str, *, error_message: str, finished_at: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE hunt_jobs
                SET status = 'failed',
                    finished_at = ?,
                    updated_at = ?,
                    last_error = ?
                WHERE id = ?
                """,
                (finished_at, finished_at, error_message[:2000], job_id),
            )

    def requeue(self, job_id: str, *, available_at: str, error_message: str, updated_at: str, hunt_id: str = "") -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE hunt_jobs
                SET status = 'queued',
                    available_at = ?,
                    updated_at = ?,
                    last_error = ?,
                    last_hunt_id = CASE WHEN ? != '' THEN ? ELSE last_hunt_id END
                WHERE id = ?
                """,
                (available_at, updated_at, error_message[:2000], hunt_id, hunt_id, job_id),
            )

    def cancel(self, job_id: str, *, updated_at: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE hunt_jobs
                SET status = 'failed',
                    finished_at = ?,
                    updated_at = ?,
                    progress_stage = 'cancelled',
                    progress_message = 'Cancelled by user',
                    last_error = CASE WHEN last_error = '' THEN 'Cancelled by user' ELSE last_error END
                WHERE id = ?
                  AND status IN ('queued', 'running')
                """,
                (updated_at, updated_at, job_id),
            )

    def retry_now(self, job_id: str, *, updated_at: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE hunt_jobs
                SET status = 'queued',
                    available_at = ?,
                    updated_at = ?,
                    finished_at = '',
                    started_at = '',
                    claimed_by = '',
                    progress_stage = 'queued',
                    progress_message = 'Waiting for consumer to claim',
                    last_error = ''
                WHERE id = ?
                  AND status IN ('failed', 'completed')
                """,
                (updated_at, updated_at, job_id),
            )

    def update_progress(
        self,
        job_id: str,
        *,
        updated_at: str,
        progress_stage: str,
        progress_message: str = "",
        hunt_id: str = "",
        template_seed_status: str | None = None,
        template_seed_source: str | None = None,
    ) -> None:
        fields = ["updated_at = ?", "progress_stage = ?", "progress_message = ?"]
        values: list[Any] = [updated_at, progress_stage, progress_message[:2000]]
        if hunt_id:
            fields.append("last_hunt_id = ?")
            values.append(hunt_id)
        if template_seed_status is not None:
            fields.append("template_seed_status = ?")
            values.append(template_seed_status)
        if template_seed_source is not None:
            fields.append("template_seed_source = ?")
            values.append(template_seed_source)
        values.append(job_id)
        with self._connect() as conn:
            conn.execute(
                f"UPDATE hunt_jobs SET {', '.join(fields)} WHERE id = ?",
                values,
            )

    def mark_template_seed_preparing(self, job_id: str, *, updated_at: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                """
                UPDATE hunt_jobs
                SET updated_at = ?,
                    template_seed_status = 'preparing',
                    progress_stage = CASE
                      WHEN progress_stage IN ('', 'queued') THEN 'template_seed'
                      ELSE progress_stage
                    END,
                    progress_message = CASE
                      WHEN progress_stage IN ('', 'queued') THEN 'Prewarming template seed before consumer claim'
                      ELSE progress_message
                    END
                WHERE id = ?
                  AND status = 'queued'
                  AND COALESCE(template_seed_status, '') IN ('', 'pending', 'failed')
                """,
                (updated_at, job_id),
            )
            return int(cur.rowcount or 0) > 0

    def attach_template_seed(self, job_id: str, *, template_seed: dict[str, Any], updated_at: str) -> None:
        job = self.get(job_id)
        if not job:
            return
        payload = job.get("payload") if isinstance(job.get("payload"), dict) else {}
        payload = dict(payload)
        payload["template_seed"] = template_seed
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE hunt_jobs
                SET payload_json = ?,
                    updated_at = ?,
                    template_seed_status = 'ready',
                    template_seed_source = ?,
                    progress_stage = CASE
                      WHEN status = 'queued' THEN 'queued'
                      ELSE progress_stage
                    END,
                    progress_message = CASE
                      WHEN status = 'queued' THEN 'Template seed prewarmed; waiting for consumer claim'
                      ELSE progress_message
                    END
                WHERE id = ?
                """,
                (
                    json.dumps(payload, ensure_ascii=False),
                    updated_at,
                    str(template_seed.get("source", "") or ""),
                    job_id,
                ),
            )

    def mark_template_seed_failed(self, job_id: str, *, error_message: str, updated_at: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE hunt_jobs
                SET updated_at = ?,
                    template_seed_status = 'failed',
                    progress_stage = CASE
                      WHEN status = 'queued' THEN 'queued'
                      ELSE progress_stage
                    END,
                    progress_message = CASE
                      WHEN status = 'queued' THEN 'Template seed prewarm failed; consumer will continue without cached seed'
                      ELSE progress_message
                    END
                WHERE id = ?
                """,
                (updated_at, job_id),
            )

    def recover_interrupted_running_jobs(self, *, updated_at: str) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """
                UPDATE hunt_jobs
                SET status = 'queued',
                    available_at = ?,
                    updated_at = ?,
                    claimed_by = '',
                    started_at = '',
                    progress_stage = 'queued',
                    progress_message = 'Recovered after API restart; waiting for consumer to reclaim',
                    last_error = CASE
                      WHEN last_error = '' THEN 'Recovered after API restart'
                      ELSE last_error
                    END
                WHERE status = 'running'
                """
                ,
                (updated_at, updated_at),
            )
            return int(cur.rowcount or 0)
