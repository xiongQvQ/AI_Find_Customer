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

# TODO: Remove once license server is deployed at https://license.aihunter.app
os.environ.setdefault("DEV_SKIP_LICENSE", "1")


def _log_dir() -> str:
    """Return a writable log directory — AppData\Roaming\AIHunter on Windows."""
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

    import uvicorn
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
