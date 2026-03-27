"""Checkpointer factory — provides persistence for LangGraph state."""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

from config.settings import get_settings


def get_checkpointer(*, in_memory: bool = False) -> MemorySaver | SqliteSaver:
    """Return a checkpointer instance.

    Args:
        in_memory: If True, use MemorySaver (for tests). Otherwise use SqliteSaver.
    """
    if in_memory:
        return MemorySaver()

    settings = get_settings()
    return SqliteSaver.from_conn_string(settings.checkpoint_db_path)
