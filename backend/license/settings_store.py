"""Read/write user .env configuration file.

Functions here are used both by the license module and by the settings API.
"""

from __future__ import annotations

import platform
import sys
from pathlib import Path


_LLM_KEYS = {"OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY", "GROQ_API_KEY",
             "ZAI_API_KEY", "MOONSHOT_API_KEY", "MINIMAX_API_KEY"}


def get_env_path() -> Path:
    """Return the path to the .env file.

    - Packaged (PyInstaller frozen): user app-data dir (survives updates).
    - Dev / bare Python: CWD/.env
    """
    if getattr(sys, "frozen", False):
        system = platform.system()
        if system == "Darwin":
            base = Path.home() / "Library" / "Application Support" / "AIHunter"
        elif system == "Windows":
            import os
            base = Path(os.environ.get("APPDATA", str(Path.home()))) / "AIHunter"
        else:
            base = Path.home() / ".config" / "AIHunter"
        base.mkdir(parents=True, exist_ok=True)
        return base / ".env"
    return Path.cwd() / ".env"


def read_settings() -> dict[str, str]:
    """Parse the .env file and return a dict of KEY -> value pairs.

    Comments (#) and blank lines are ignored.
    Values containing '=' are handled correctly (split on first '=' only).
    """
    path = get_env_path()
    if not path.exists():
        return {}
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def write_settings(data: dict[str, str]) -> None:
    """Write *data* to the .env file, replacing its entire contents."""
    path = get_env_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{k}={v}\n" for k, v in data.items()]
    path.write_text("".join(lines), encoding="utf-8")


def update_settings(updates: dict[str, str]) -> None:
    """Merge *updates* into the existing .env file (create if missing)."""
    existing = read_settings()
    existing.update(updates)
    write_settings(existing)


def is_configured() -> bool:
    """Return True if at least one LLM API key is present in the .env."""
    settings = read_settings()
    return any(settings.get(k, "").strip() for k in _LLM_KEYS)
