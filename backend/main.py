"""AI Hunter backend entry point.

This file is the PyInstaller entry point (build_backend.sh targets main.py).
It starts the FastAPI server via uvicorn on localhost:8000.

In packaged mode (sys.frozen=True), config/settings.py automatically loads
.env from the user's app-data directory instead of the CWD.
"""

import multiprocessing
import os
import sys
import traceback

import uvicorn


def _log_dir() -> str:
    """Return a writable log directory — AppData\\Roaming\\AIHunter on Windows."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.path.expanduser("~/.local/share")
    d = os.path.join(base, "AIHunter", "logs")
    os.makedirs(d, exist_ok=True)
    return d


def main() -> None:
    # Required on Windows for PyInstaller + multiprocessing
    multiprocessing.freeze_support()

    # Under PyInstaller --noconsole, sys.stdout/stderr are None.
    # uvicorn's logging setup calls stream.isatty() and crashes if stream is None.
    # Redirect to the log file so uvicorn output is captured.
    if sys.stdout is None or sys.stderr is None:
        log_path = os.path.join(_log_dir(), "backend.log")
        _f = open(log_path, "a", buffering=1, encoding="utf-8")
        if sys.stdout is None:
            sys.stdout = _f
        if sys.stderr is None:
            sys.stderr = _f

    uvicorn.run(
        "api.app:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
        workers=1,
        reload=False,
        access_log=False,
    )


if __name__ == "__main__":
    log_file = os.path.join(_log_dir(), "backend_startup.log")
    try:
        main()
    except Exception:
        with open(log_file, "w") as f:
            traceback.print_exc(file=f)
        raise
