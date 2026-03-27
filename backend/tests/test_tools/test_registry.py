"""Tests for tools/registry.py — register, get, has, duplicate, missing."""

import pytest

from tools.registry import ToolRegistry


class TestToolRegistry:
    def test_register_and_get(self):
        reg = ToolRegistry()
        reg.register("llm", "fake_llm")
        assert reg.get("llm") == "fake_llm"

    def test_get_missing_raises(self):
        reg = ToolRegistry()
        with pytest.raises(KeyError, match="not found"):
            reg.get("nonexistent")

    def test_duplicate_register_raises(self):
        reg = ToolRegistry()
        reg.register("llm", "v1")
        with pytest.raises(ValueError, match="already registered"):
            reg.register("llm", "v2")

    def test_has(self):
        reg = ToolRegistry()
        assert reg.has("llm") is False
        reg.register("llm", "x")
        assert reg.has("llm") is True

    def test_contains(self):
        reg = ToolRegistry()
        reg.register("search", "s")
        assert "search" in reg
        assert "missing" not in reg

    def test_names(self):
        reg = ToolRegistry()
        reg.register("a", 1)
        reg.register("b", 2)
        assert set(reg.names) == {"a", "b"}

    def test_len(self):
        reg = ToolRegistry()
        assert len(reg) == 0
        reg.register("x", 1)
        assert len(reg) == 1

    def test_multiple_tools(self):
        reg = ToolRegistry()
        reg.register("llm", "llm_tool")
        reg.register("jina", "jina_tool")
        reg.register("search", "search_tool")
        assert len(reg) == 3
        assert reg.get("jina") == "jina_tool"
