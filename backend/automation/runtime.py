"""In-process runtime state for embedded automation workers."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


_RUNTIME_STATE: dict[str, dict[str, Any]] = {
    "consumer": {
        "enabled": False,
        "running": False,
        "worker_id": "",
        "active_job_id": "",
        "last_claimed_job_id": "",
        "last_completed_job_id": "",
        "last_error": "",
        "last_poll_at": "",
        "last_activity_at": "",
    }
}


def update_worker_state(worker: str, **updates: Any) -> None:
    state = _RUNTIME_STATE.setdefault(worker, {})
    state.update(updates)


def get_runtime_state() -> dict[str, dict[str, Any]]:
    return deepcopy(_RUNTIME_STATE)
