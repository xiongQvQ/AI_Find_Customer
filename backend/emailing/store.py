"""SQLite store for email automation state."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


_DDL = """
CREATE TABLE IF NOT EXISTS email_accounts (
  id TEXT PRIMARY KEY,
  provider_type TEXT NOT NULL,
  from_name TEXT NOT NULL,
  from_email TEXT NOT NULL,
  reply_to TEXT DEFAULT '',
  smtp_host TEXT DEFAULT '',
  smtp_port INTEGER DEFAULT 587,
  smtp_username TEXT DEFAULT '',
  smtp_secret_encrypted TEXT DEFAULT '',
  imap_host TEXT DEFAULT '',
  imap_port INTEGER DEFAULT 993,
  imap_username TEXT DEFAULT '',
  imap_secret_encrypted TEXT DEFAULT '',
  use_tls INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'active',
  daily_send_limit INTEGER NOT NULL DEFAULT 50,
  hourly_send_limit INTEGER NOT NULL DEFAULT 10,
  last_test_at TEXT DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS email_campaigns (
  id TEXT PRIMARY KEY,
  hunt_id TEXT NOT NULL,
  email_account_id TEXT NOT NULL,
  name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft',
  language_mode TEXT NOT NULL DEFAULT 'auto_by_region',
  default_language TEXT NOT NULL DEFAULT 'en',
  fallback_language TEXT NOT NULL DEFAULT 'en',
  tone TEXT NOT NULL DEFAULT 'professional',
  step1_delay_days INTEGER NOT NULL DEFAULT 0,
  step2_delay_days INTEGER NOT NULL DEFAULT 3,
  step3_delay_days INTEGER NOT NULL DEFAULT 3,
  min_fit_score REAL NOT NULL DEFAULT 0.6,
  min_contactability_score REAL NOT NULL DEFAULT 0.45,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS lead_email_sequences (
  id TEXT PRIMARY KEY,
  campaign_id TEXT NOT NULL,
  hunt_id TEXT NOT NULL,
  lead_key TEXT NOT NULL,
  lead_email TEXT NOT NULL,
  lead_name TEXT DEFAULT '',
  decision_maker_name TEXT DEFAULT '',
  decision_maker_title TEXT DEFAULT '',
  locale TEXT NOT NULL DEFAULT 'en',
  generation_mode TEXT NOT NULL DEFAULT 'personalized',
  template_id TEXT DEFAULT '',
  template_group TEXT DEFAULT '',
  template_usage_index INTEGER NOT NULL DEFAULT 0,
  template_max_send_count INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'draft',
  current_step INTEGER NOT NULL DEFAULT 0,
  stop_reason TEXT DEFAULT '',
  replied_at TEXT DEFAULT '',
  last_sent_at TEXT DEFAULT '',
  next_scheduled_at TEXT DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_sequence_campaign_lead ON lead_email_sequences(campaign_id, lead_key);
CREATE TABLE IF NOT EXISTS email_messages (
  id TEXT PRIMARY KEY,
  sequence_id TEXT NOT NULL,
  step_number INTEGER NOT NULL,
  goal TEXT NOT NULL,
  locale TEXT NOT NULL,
  subject TEXT NOT NULL,
  body_text TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  scheduled_at TEXT NOT NULL,
  sent_at TEXT DEFAULT '',
  provider_message_id TEXT DEFAULT '',
  thread_key TEXT DEFAULT '',
  failure_reason TEXT DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_email_message_sequence_step ON email_messages(sequence_id, step_number);
CREATE INDEX IF NOT EXISTS idx_email_message_status_schedule ON email_messages(status, scheduled_at);
CREATE TABLE IF NOT EXISTS email_reply_events (
  id TEXT PRIMARY KEY,
  sequence_id TEXT NOT NULL,
  message_id TEXT DEFAULT '',
  from_email TEXT NOT NULL,
  subject TEXT DEFAULT '',
  snippet TEXT DEFAULT '',
  received_at TEXT NOT NULL,
  raw_ref TEXT DEFAULT '',
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_reply_sequence_id ON email_reply_events(sequence_id);
"""


class EmailStore:
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
            self._ensure_column(conn, "lead_email_sequences", "generation_mode", "TEXT NOT NULL DEFAULT 'personalized'")
            self._ensure_column(conn, "lead_email_sequences", "template_id", "TEXT DEFAULT ''")
            self._ensure_column(conn, "lead_email_sequences", "template_group", "TEXT DEFAULT ''")
            self._ensure_column(conn, "lead_email_sequences", "template_usage_index", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(conn, "lead_email_sequences", "template_max_send_count", "INTEGER NOT NULL DEFAULT 0")

    def _ensure_column(self, conn: sqlite3.Connection, table_name: str, column_name: str, definition: str) -> None:
        columns = {
            row["name"]
            for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        }
        if column_name not in columns:
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")

    def upsert_account(self, payload: dict[str, Any]) -> None:
        cols = [
            "id", "provider_type", "from_name", "from_email", "reply_to",
            "smtp_host", "smtp_port", "smtp_username", "smtp_secret_encrypted",
            "imap_host", "imap_port", "imap_username", "imap_secret_encrypted",
            "use_tls", "status", "daily_send_limit", "hourly_send_limit",
            "last_test_at", "created_at", "updated_at",
        ]
        values = [payload.get(col, "") for col in cols]
        placeholders = ", ".join("?" for _ in cols)
        updates = ", ".join(f"{col}=excluded.{col}" for col in cols[1:])
        with self._connect() as conn:
            conn.execute(
                f"INSERT INTO email_accounts ({', '.join(cols)}) VALUES ({placeholders}) "
                f"ON CONFLICT(id) DO UPDATE SET {updates}",
                values,
            )

    def get_account(self, account_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM email_accounts WHERE id = ?", (account_id,)).fetchone()
        return dict(row) if row else None

    def create_campaign(self, payload: dict[str, Any]) -> None:
        cols = list(payload.keys())
        with self._connect() as conn:
            conn.execute(
                f"INSERT INTO email_campaigns ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
                [payload[c] for c in cols],
            )

    def get_campaign(self, campaign_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM email_campaigns WHERE id = ?", (campaign_id,)).fetchone()
        return dict(row) if row else None

    def list_campaigns_for_hunt(self, hunt_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM email_campaigns WHERE hunt_id = ? ORDER BY created_at DESC",
                (hunt_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def update_campaign_status(self, campaign_id: str, status: str, *, updated_at: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE email_campaigns SET status = ?, updated_at = ? WHERE id = ?",
                (status, updated_at, campaign_id),
            )

    def create_sequence(self, payload: dict[str, Any]) -> None:
        cols = list(payload.keys())
        with self._connect() as conn:
            conn.execute(
                f"INSERT INTO lead_email_sequences ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
                [payload[c] for c in cols],
            )

    def get_sequence(self, sequence_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM lead_email_sequences WHERE id = ?", (sequence_id,)).fetchone()
        return dict(row) if row else None

    def list_sequences_for_campaign(self, campaign_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM lead_email_sequences WHERE campaign_id = ? ORDER BY created_at ASC",
                (campaign_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def has_contact_history_for_lead_key(self, lead_key: str) -> bool:
        """Return whether a lead/email pair was already queued or contacted before.

        Purely failed sequences with no sent messages do not block retry.
        """
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT 1
                FROM lead_email_sequences seq
                LEFT JOIN email_messages msg
                  ON msg.sequence_id = seq.id
                 AND msg.status = 'sent'
                WHERE seq.lead_key = ?
                  AND (
                    seq.status != 'failed'
                    OR msg.id IS NOT NULL
                  )
                LIMIT 1
                """,
                (lead_key,),
            ).fetchone()
        return row is not None

    def update_sequence_status(
        self,
        sequence_id: str,
        *,
        status: str,
        updated_at: str,
        current_step: int | None = None,
        stop_reason: str | None = None,
        replied_at: str | None = None,
        last_sent_at: str | None = None,
        next_scheduled_at: str | None = None,
    ) -> None:
        fields = ["status = ?", "updated_at = ?"]
        values: list[Any] = [status, updated_at]
        for name, value in [
            ("current_step", current_step),
            ("stop_reason", stop_reason),
            ("replied_at", replied_at),
            ("last_sent_at", last_sent_at),
            ("next_scheduled_at", next_scheduled_at),
        ]:
            if value is not None:
                fields.append(f"{name} = ?")
                values.append(value)
        values.append(sequence_id)
        with self._connect() as conn:
            conn.execute(
                f"UPDATE lead_email_sequences SET {', '.join(fields)} WHERE id = ?",
                values,
            )

    def create_message(self, payload: dict[str, Any]) -> None:
        cols = list(payload.keys())
        with self._connect() as conn:
            conn.execute(
                f"INSERT INTO email_messages ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
                [payload[c] for c in cols],
            )

    def get_message(self, message_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM email_messages WHERE id = ?", (message_id,)).fetchone()
        return dict(row) if row else None

    def find_message_by_provider_message_id(self, provider_message_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM email_messages WHERE provider_message_id = ? LIMIT 1",
                (provider_message_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_message_for_step(self, sequence_id: str, step_number: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM email_messages WHERE sequence_id = ? AND step_number = ?",
                (sequence_id, step_number),
            ).fetchone()
        return dict(row) if row else None

    def list_messages_for_sequence(self, sequence_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM email_messages WHERE sequence_id = ? ORDER BY step_number ASC",
                (sequence_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_pending_messages_ready(self, now_iso: str, *, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM email_messages WHERE status = 'pending' AND scheduled_at <= ? "
                "ORDER BY scheduled_at ASC LIMIT ?",
                (now_iso, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def mark_message_sent(self, message_id: str, *, provider_message_id: str, thread_key: str, sent_at: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE email_messages SET status = 'sent', provider_message_id = ?, thread_key = ?, sent_at = ?, updated_at = ? WHERE id = ?",
                (provider_message_id, thread_key, sent_at, sent_at, message_id),
            )

    def mark_message_failed(self, message_id: str, *, failure_reason: str, updated_at: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE email_messages SET status = 'failed', failure_reason = ?, updated_at = ? WHERE id = ?",
                (failure_reason, updated_at, message_id),
            )

    def cancel_future_pending_messages(self, sequence_id: str, *, updated_at: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE email_messages SET status = 'cancelled', updated_at = ? WHERE sequence_id = ? AND status = 'pending'",
                (updated_at, sequence_id),
            )

    def count_messages_for_campaign(self, campaign_id: str, *, status: str | None = None) -> int:
        query = (
            "SELECT COUNT(*) FROM email_messages m "
            "JOIN lead_email_sequences s ON s.id = m.sequence_id "
            "WHERE s.campaign_id = ?"
        )
        params: list[Any] = [campaign_id]
        if status:
            query += " AND m.status = ?"
            params.append(status)
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        return int(row[0]) if row else 0

    def count_messages_by_status(self, status: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM email_messages WHERE status = ?",
                (status,),
            ).fetchone()
        return int(row[0]) if row else 0

    def count_sequences_by_status(self, *statuses: str) -> int:
        if not statuses:
            return 0
        placeholders = ", ".join("?" for _ in statuses)
        with self._connect() as conn:
            row = conn.execute(
                f"SELECT COUNT(*) FROM lead_email_sequences WHERE status IN ({placeholders})",
                list(statuses),
            ).fetchone()
        return int(row[0]) if row else 0

    def count_campaigns_by_status(self, *statuses: str) -> int:
        if not statuses:
            return 0
        placeholders = ", ".join("?" for _ in statuses)
        with self._connect() as conn:
            row = conn.execute(
                f"SELECT COUNT(*) FROM email_campaigns WHERE status IN ({placeholders})",
                list(statuses),
            ).fetchone()
        return int(row[0]) if row else 0

    def count_messages_since(self, status: str, *, since_iso: str, time_field: str = "updated_at") -> int:
        if time_field not in {"created_at", "updated_at", "scheduled_at", "sent_at"}:
            raise ValueError("Unsupported time field")
        with self._connect() as conn:
            row = conn.execute(
                f"SELECT COUNT(*) FROM email_messages WHERE status = ? AND {time_field} >= ?",
                (status, since_iso),
            ).fetchone()
        return int(row[0]) if row else 0

    def find_sent_message_by_lead_email_and_subject(self, lead_email: str, subject: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT m.* FROM email_messages m "
                "JOIN lead_email_sequences s ON s.id = m.sequence_id "
                "WHERE m.status = 'sent' AND lower(s.lead_email) = lower(?) AND lower(m.subject) = lower(?) "
                "ORDER BY m.sent_at DESC LIMIT 1",
                (lead_email, subject),
            ).fetchone()
        return dict(row) if row else None

    def has_reply_event(self, raw_ref: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM email_reply_events WHERE raw_ref = ? LIMIT 1",
                (raw_ref,),
            ).fetchone()
        return row is not None

    def create_reply_event(self, payload: dict[str, Any]) -> None:
        cols = list(payload.keys())
        with self._connect() as conn:
            conn.execute(
                f"INSERT INTO email_reply_events ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
                [payload[c] for c in cols],
            )

    def list_reply_events_for_sequence(self, sequence_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM email_reply_events WHERE sequence_id = ? ORDER BY received_at DESC",
                (sequence_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def count_reply_events_since(self, since_iso: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM email_reply_events WHERE received_at >= ?",
                (since_iso,),
            ).fetchone()
        return int(row[0]) if row else 0

    def list_recent_message_failures(self, *, since_iso: str, limit: int = 10) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT m.subject, m.failure_reason, m.updated_at, s.lead_email
                FROM email_messages m
                JOIN lead_email_sequences s ON s.id = m.sequence_id
                WHERE m.status = 'failed' AND m.updated_at >= ?
                ORDER BY m.updated_at DESC
                LIMIT ?
                """,
                (since_iso, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_sent_messages_since(self, *, since_iso: str, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                  m.id,
                  m.subject,
                  m.sent_at,
                  s.lead_email,
                  s.lead_name,
                  s.hunt_id,
                  s.campaign_id
                FROM email_messages m
                JOIN lead_email_sequences s ON s.id = m.sequence_id
                WHERE m.status = 'sent' AND m.sent_at >= ?
                ORDER BY m.sent_at ASC, m.id ASC
                LIMIT ?
                """,
                (since_iso, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_reply_events_since(self, *, since_iso: str, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                  r.id,
                  r.from_email,
                  r.subject,
                  r.snippet,
                  r.received_at,
                  s.lead_name,
                  s.hunt_id,
                  s.campaign_id
                FROM email_reply_events r
                JOIN lead_email_sequences s ON s.id = r.sequence_id
                WHERE r.received_at >= ?
                ORDER BY r.received_at DESC, r.id DESC
                LIMIT ?
                """,
                (since_iso, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_message_failure_reasons(self, *, since_iso: str, limit: int = 5) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT failure_reason, COUNT(*) AS count
                FROM email_messages
                WHERE status = 'failed' AND updated_at >= ?
                GROUP BY failure_reason
                ORDER BY count DESC, failure_reason ASC
                LIMIT ?
                """,
                (since_iso, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_template_performance_for_campaign(
        self,
        campaign_id: str,
        *,
        underperforming_min_assigned: int = 10,
        underperforming_min_reply_rate: float = 1.0,
    ) -> dict[str, dict[str, Any]]:
        sequences = [seq for seq in self.list_sequences_for_campaign(campaign_id) if seq.get("template_id")]
        if not sequences:
            return {}

        template_summary: dict[str, dict[str, Any]] = {}
        with self._connect() as conn:
            for sequence in sequences:
                template_id = str(sequence.get("template_id") or "")
                if not template_id:
                    continue
                summary = template_summary.setdefault(
                    template_id,
                    {
                        "template_id": template_id,
                        "template_group": str(sequence.get("template_group") or ""),
                        "generation_mode": str(sequence.get("generation_mode") or "template_pool"),
                        "assigned_count": 0,
                        "max_send_count": int(sequence.get("template_max_send_count") or 0),
                        "sent_count": 0,
                        "replied_count": 0,
                        "reply_rate": 0.0,
                        "remaining_capacity": 0,
                        "status": "warming_up",
                        "optimization_needed": False,
                        "recommended_action": "keep_collecting_data",
                        "reason": "Not enough delivery/reply data yet.",
                    },
                )
                summary["assigned_count"] += 1
                if sequence.get("status") == "replied":
                    summary["replied_count"] += 1

                row = conn.execute(
                    "SELECT COUNT(*) FROM email_messages WHERE sequence_id = ? AND status = 'sent'",
                    (sequence["id"],),
                ).fetchone()
                summary["sent_count"] += int(row[0]) if row else 0

        for summary in template_summary.values():
            assigned = int(summary["assigned_count"])
            replied = int(summary["replied_count"])
            max_send_count = int(summary["max_send_count"])
            summary["reply_rate"] = round((replied / assigned) * 100, 2) if assigned else 0.0
            summary["remaining_capacity"] = max(max_send_count - assigned, 0)
            if max_send_count and assigned >= max_send_count:
                summary["status"] = "exhausted"
                summary["optimization_needed"] = True
                summary["recommended_action"] = "create_new_template_version"
                summary["reason"] = "Template reached the configured assignment cap."
            elif assigned >= underperforming_min_assigned and summary["reply_rate"] < underperforming_min_reply_rate:
                summary["status"] = "underperforming"
                summary["optimization_needed"] = True
                summary["recommended_action"] = "optimize_template_before_more_sends"
                summary["reason"] = (
                    f"Reply rate {summary['reply_rate']}% is below the threshold "
                    f"{underperforming_min_reply_rate}% after {assigned} assignments."
                )
            else:
                summary["status"] = "warming_up"
                summary["optimization_needed"] = False
                summary["recommended_action"] = "keep_collecting_data"
                summary["reason"] = "Continue sending until enough reply data accumulates."
        return template_summary
