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
  last_hunt_id TEXT DEFAULT ''
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

    def enqueue(self, payload: dict[str, Any], *, now_iso: str, available_at: str | None = None) -> str:
        job_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO hunt_jobs (
                  id, payload_json, status, available_at, created_at, updated_at
                ) VALUES (?, ?, 'queued', ?, ?, ?)
                """,
                (
                    job_id,
                    json.dumps(payload, ensure_ascii=False),
                    available_at or now_iso,
                    now_iso,
                    now_iso,
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
                WHERE status = 'queued' AND available_at <= ?
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
                    last_error = ''
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
