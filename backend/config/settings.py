"""Application settings managed via pydantic-settings."""

import os
import platform
import sys
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _app_data_dir() -> Path | None:
    """Return the user's writable app-data directory when running packaged.

    Returns None in dev mode so callers fall back to relative paths.
    """
    if not getattr(sys, "frozen", False):
        return None
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("APPDATA", str(Path.home())))
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".config"
    app_dir = base / "AIHunter"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def _resolve_env_file() -> str:
    """Return the .env path to use.

    - Packaged (PyInstaller frozen binary): user app-data dir so the file
      survives app updates and is writable by the user.
    - Dev / bare Python: local .env next to the current working directory.
    """
    d = _app_data_dir()
    if d is not None:
        return str(d / ".env")
    return ".env"


def _resolve_dir(relative: str) -> str:
    """Resolve a writable directory path (created if missing in packaged mode)."""
    d = _app_data_dir()
    if d is not None:
        resolved = d / relative
        resolved.mkdir(parents=True, exist_ok=True)
        return str(resolved)
    return relative


def _resolve_file(relative: str) -> str:
    """Resolve a writable file path (parent dir created if missing in packaged mode)."""
    d = _app_data_dir()
    if d is not None:
        resolved = d / relative
        resolved.parent.mkdir(parents=True, exist_ok=True)
        return str(resolved)
    return relative


class Settings(BaseSettings):
    """AI Hunter configuration — loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=_resolve_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- LLM (litellm model format: "provider/model") ---
    # Active model — uses litellm naming, e.g.:
    #   "gpt-4o"                        (OpenAI)
    #   "anthropic/claude-3-5-sonnet-20241022"  (Anthropic)
    #   "openrouter/google/gemini-pro"  (OpenRouter)
    #   "groq/llama-3.3-70b-versatile"  (Groq)
    #   "zai/glm-4.7"                   (GLM / 智谱 Z.AI)
    #   "moonshot/moonshot-v1-128k"      (Kimi / Moonshot)
    #   "minimax/MiniMax-Text-01"        (MiniMax)
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 4096

    # Reasoning model — used for ReAct agent decision-making (stronger reasoning)
    #   e.g. "gpt-4o", "anthropic/claude-3-5-sonnet-20241022", "openrouter/deepseek/deepseek-r1"
    reasoning_model: str = "gpt-4o"
    reasoning_temperature: float = 0.2
    reasoning_max_tokens: int = 4096

    # --- LLM Provider API Keys ---
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    openrouter_api_key: str = ""
    groq_api_key: str = ""
    zai_api_key: str = ""         # GLM / 智谱 Z.AI
    moonshot_api_key: str = ""    # Kimi / Moonshot AI
    minimax_api_key: str = ""
    minimax_api_base: str = "https://api.minimax.io/v1"

    # --- Search ---
    # Google Maps search: always uses Serper (single key)
    serper_api_key: str = ""
    # General web search: Tavily (primary) → Serper (fallback).
    # Tavily supports multiple keys (comma-separated) for round-robin rotation.
    tavily_api_key: str = ""      # e.g. "key1,key2"
    jina_api_key: str = ""
    amap_api_key: str = ""        # 高德地图 Web API key
    baidu_api_key: str = ""       # 百度千帆 AppBuilder API key (for baidu web search)

    # --- Email ---
    hunter_api_key: str = ""

    # --- Langfuse (observability) ---
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://localhost:3000"
    langfuse_enabled: bool = False

    # --- Hunt defaults ---
    default_target_lead_count: int = 200
    default_max_rounds: int = 10
    default_keywords_per_round: int = 8
    min_new_leads_threshold: int = 5  # stop if fewer new leads per round

    # --- Concurrency ---
    search_concurrency: int = 10  # max concurrent Serper API calls
    scrape_concurrency: int = 5   # max concurrent Jina Reader calls
    email_gen_concurrency: int = 3  # max concurrent LLM calls for email generation
    react_max_iterations: int = 5   # max ReAct loop iterations per URL

    # --- API ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # --- Database (checkpointer) ---
    # In packaged mode, redirected to ~/Library/Application Support/AIHunter/
    checkpoint_db_path: str = _resolve_file("hunt_sessions.db")

    # --- License ---
    license_server_url: str = "https://aihunter-license-worker.xiongbojian007.workers.dev"

    # --- Hunt persistence ---
    hunts_dir: str = _resolve_dir("data/hunts")  # directory for JSON hunt files

    # --- File upload ---
    upload_dir: str = _resolve_dir("uploads")
    max_upload_size_mb: int = 50


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
