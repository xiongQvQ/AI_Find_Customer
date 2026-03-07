"""Machine fingerprint generation.

Produces a stable 32-char hex ID from hardware/OS attributes.
The result is cached to ~/.aihunter/.machine_id so it survives
minor hardware changes (e.g. USB devices, network adapters).
"""

from __future__ import annotations

import hashlib
import platform
import subprocess
from pathlib import Path


_CACHE_FILE = Path.home() / ".aihunter" / ".machine_id"


def _safe_run(cmd: list[str]) -> str:
    """Run a subprocess command and return stdout, or '' on any error."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        return result.stdout.strip()
    except Exception:
        return ""


def _get_mac_addresses() -> str:
    """Return a sorted, joined string of non-loopback MAC addresses."""
    try:
        import uuid as _uuid
        # uuid.getnode() returns the MAC as an integer
        mac = _uuid.getnode()
        return format(mac, "012x")
    except Exception:
        return ""


def _get_disk_serial() -> str:
    """Return disk serial number where available (macOS only for now)."""
    system = platform.system()
    if system == "Darwin":
        out = _safe_run(["system_profiler", "SPStorageDataType"])
        for line in out.splitlines():
            if "Serial" in line or "serial" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    return parts[1].strip()
    elif system == "Windows":
        out = _safe_run(["wmic", "diskdrive", "get", "SerialNumber"])
        lines = [l.strip() for l in out.splitlines() if l.strip() and "SerialNumber" not in l]
        if lines:
            return lines[0]
    return ""


def _compute_machine_id() -> str:
    """Compute a fresh machine ID from hardware attributes."""
    components = [
        platform.node(),
        platform.machine(),
        platform.processor(),
        _get_mac_addresses(),
        _get_disk_serial(),
    ]
    raw = "|".join(c for c in components if c)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def get_machine_id() -> str:
    """Return a stable 32-char hex machine ID.

    The ID is cached to disk so that minor hardware changes (e.g. USB
    devices, network adapters) don't break an existing activation.

    The disk cache is only trusted when the current ``platform.node()``
    matches what the cache was built on — that way test patches to
    ``platform.node`` are reflected correctly.
    """
    current_node = platform.node()

    # Check disk cache: stored as "<node_hash>:<machine_id>"
    expected_node_hash = hashlib.sha256(current_node.encode()).hexdigest()[:16]
    if _CACHE_FILE.exists():
        try:
            raw = _CACHE_FILE.read_text().strip()
            if ":" in raw:
                node_hash, cached_mid = raw.split(":", 1)
                if node_hash == expected_node_hash and len(cached_mid) == 32:
                    return cached_mid
                # node hash mismatch — fall through to recompute
            # Legacy format (plain 32-char hex, no node prefix) — do NOT trust;
            # recompute so that tests patching platform.node() see new values.
        except OSError:
            pass

    mid = _compute_machine_id()
    try:
        _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        node_hash = hashlib.sha256(current_node.encode()).hexdigest()[:16]
        _CACHE_FILE.write_text(f"{node_hash}:{mid}")
    except OSError:
        pass
    return mid
