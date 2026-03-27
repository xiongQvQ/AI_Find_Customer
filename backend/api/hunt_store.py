"""Hunt persistence — JSON file-based storage for hunt metadata and results.

Each hunt is saved as a JSON file: {hunts_dir}/{hunt_id}.json
On server startup, all existing hunt files are loaded into the in-memory _hunts dict.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import get_settings

logger = logging.getLogger(__name__)


def _hunts_dir() -> Path:
    """Return the hunts directory path, creating it if needed."""
    settings = get_settings()
    p = Path(settings.hunts_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_hunt(hunt_id: str, hunt_data: dict[str, Any]) -> None:
    """Persist a hunt to disk as JSON."""
    try:
        path = _hunts_dir() / f"{hunt_id}.json"
        payload = {"hunt_id": hunt_id, **hunt_data}
        path.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")
    except Exception as e:
        logger.warning("[HuntStore] Failed to save hunt %s: %s", hunt_id[:8], e)


def load_all_hunts() -> dict[str, dict[str, Any]]:
    """Load all hunts from disk into a dict keyed by hunt_id."""
    hunts: dict[str, dict[str, Any]] = {}
    hunts_path = _hunts_dir()

    for path in hunts_path.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            hid = data.pop("hunt_id", path.stem)
            # Any hunt that was running/pending when the process died is now interrupted
            if data.get("status") in ("running", "pending"):
                data["status"] = "failed"
                data["error"] = "Process was interrupted (server restarted)"
                data["completed_at"] = now_iso()
                # Persist the updated status so it survives future restarts
                payload = {"hunt_id": hid, **data}
                path.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")
                logger.info("[HuntStore] Marked interrupted hunt %s as failed", hid[:8])
            hunts[hid] = data
            logger.debug("[HuntStore] Loaded hunt %s (status=%s)", hid[:8], data.get("status"))
        except Exception as e:
            logger.warning("[HuntStore] Failed to load %s: %s", path.name, e)

    if hunts:
        logger.info("[HuntStore] Loaded %d historical hunts from %s", len(hunts), hunts_path)
    return hunts


def delete_hunt(hunt_id: str) -> None:
    """Delete a hunt file from disk."""
    try:
        path = _hunts_dir() / f"{hunt_id}.json"
        if path.exists():
            path.unlink()
    except Exception as e:
        logger.warning("[HuntStore] Failed to delete hunt %s: %s", hunt_id[:8], e)


def load_hunt(hunt_id: str) -> dict[str, Any] | None:
    """Load a single hunt from disk."""
    try:
        path = _hunts_dir() / f"{hunt_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        data.pop("hunt_id", None)
        return data
    except Exception as e:
        logger.warning("[HuntStore] Failed to load hunt %s: %s", hunt_id[:8], e)
        return None


def now_iso() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()
