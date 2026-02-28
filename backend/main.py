"""AI Hunter backend entry point.

This file is the PyInstaller entry point (build_backend.sh targets main.py).
It starts the FastAPI server via uvicorn on localhost:8000.

In packaged mode (sys.frozen=True), config/settings.py automatically loads
.env from the user's app-data directory instead of the CWD.
"""

import multiprocessing
import sys

import uvicorn


def main() -> None:
    # Required on Windows for PyInstaller + multiprocessing
    multiprocessing.freeze_support()

    uvicorn.run(
        "api.app:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
        # Single worker — the app uses asyncio concurrency internally
        workers=1,
        # Don't reload in production
        reload=False,
        # Access log off to reduce noise in packaged binary
        access_log=False,
    )


if __name__ == "__main__":
    main()
