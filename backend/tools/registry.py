"""Unified tool registry — all tools register here and agents look them up by name."""

from __future__ import annotations

from typing import Any


class ToolRegistry:
    """Central registry for all tools/skills available to agents.

    Usage:
        registry = ToolRegistry()
        registry.register("llm", llm_tool)
        registry.register("jina_reader", jina_tool)

        llm = registry.get("llm")
    """

    def __init__(self) -> None:
        self._tools: dict[str, Any] = {}

    def register(self, name: str, tool: Any) -> None:
        """Register a tool by name. Raises if name already taken."""
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered")
        self._tools[name] = tool

    def get(self, name: str) -> Any:
        """Retrieve a tool by name. Raises KeyError if not found."""
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found. Available: {list(self._tools.keys())}")
        return self._tools[name]

    def has(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    @property
    def names(self) -> list[str]:
        """Return all registered tool names."""
        return list(self._tools.keys())

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
