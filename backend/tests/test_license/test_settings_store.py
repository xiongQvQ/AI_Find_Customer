"""Tests for config/settings_store.py"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from config.settings_store import (
    get_env_path,
    is_configured,
    read_settings,
    update_settings,
    write_settings,
)


@pytest.fixture()
def env_file(tmp_path):
    """Patch get_env_path to return a temp file."""
    p = tmp_path / ".env"
    with patch("config.settings_store.get_env_path", return_value=p):
        yield p


class TestGetEnvPath:
    def test_dev_mode_returns_cwd_env(self):
        """In non-frozen mode, returns CWD/.env"""
        # sys.frozen is not set in test environment
        path = get_env_path()
        assert path.name == ".env"
        assert path == Path.cwd() / ".env"

    def test_frozen_mode_returns_app_data(self, tmp_path):
        """In frozen (packaged) mode, returns app-data dir"""
        with patch.object(sys, "frozen", True, create=True):
            with patch("platform.system", return_value="Darwin"):
                with patch("pathlib.Path.home", return_value=tmp_path):
                    path = get_env_path()
        assert "AIHunter" in str(path)
        assert path.name == ".env"


class TestReadSettings:
    def test_returns_empty_dict_when_no_file(self, env_file):
        assert not env_file.exists()
        result = read_settings()
        assert result == {}

    def test_parses_key_value_pairs(self, env_file):
        env_file.write_text("OPENAI_API_KEY=sk-test\nSERPER_API_KEY=serp-key\n")
        result = read_settings()
        assert result["OPENAI_API_KEY"] == "sk-test"
        assert result["SERPER_API_KEY"] == "serp-key"

    def test_ignores_comments(self, env_file):
        env_file.write_text("# This is a comment\nOPENAI_API_KEY=sk-test\n")
        result = read_settings()
        assert "# This is a comment" not in result
        assert result["OPENAI_API_KEY"] == "sk-test"

    def test_ignores_blank_lines(self, env_file):
        env_file.write_text("\nOPENAI_API_KEY=sk-test\n\n")
        result = read_settings()
        assert result == {"OPENAI_API_KEY": "sk-test"}

    def test_value_with_equals_sign(self, env_file):
        env_file.write_text("DATABASE_URL=postgres://user:pass@host/db\n")
        result = read_settings()
        assert result["DATABASE_URL"] == "postgres://user:pass@host/db"


class TestWriteSettings:
    def test_writes_key_value_pairs(self, env_file):
        write_settings({"OPENAI_API_KEY": "sk-abc", "SERPER_API_KEY": "serp-xyz"})
        content = env_file.read_text()
        assert "OPENAI_API_KEY=sk-abc" in content
        assert "SERPER_API_KEY=serp-xyz" in content

    def test_overwrites_existing_file(self, env_file):
        env_file.write_text("OLD_KEY=old-value\n")
        write_settings({"NEW_KEY": "new-value"})
        content = env_file.read_text()
        assert "OLD_KEY" not in content
        assert "NEW_KEY=new-value" in content


class TestUpdateSettings:
    def test_merges_with_existing(self, env_file):
        env_file.write_text("OPENAI_API_KEY=existing\n")
        update_settings({"SERPER_API_KEY": "new-serp"})
        result = read_settings()
        assert result["OPENAI_API_KEY"] == "existing"
        assert result["SERPER_API_KEY"] == "new-serp"

    def test_overwrites_existing_key(self, env_file):
        env_file.write_text("OPENAI_API_KEY=old\n")
        update_settings({"OPENAI_API_KEY": "new"})
        result = read_settings()
        assert result["OPENAI_API_KEY"] == "new"

    def test_creates_file_if_missing(self, env_file):
        assert not env_file.exists()
        update_settings({"SERPER_API_KEY": "abc"})
        assert env_file.exists()
        assert read_settings()["SERPER_API_KEY"] == "abc"


class TestIsConfigured:
    def test_false_when_no_file(self, env_file):
        assert is_configured() is False

    def test_true_with_openai_key(self, env_file):
        env_file.write_text("OPENAI_API_KEY=sk-test\n")
        assert is_configured() is True

    def test_true_with_anthropic_key(self, env_file):
        env_file.write_text("ANTHROPIC_API_KEY=ant-test\n")
        assert is_configured() is True

    def test_true_with_openrouter_key(self, env_file):
        env_file.write_text("OPENROUTER_API_KEY=or-test\n")
        assert is_configured() is True

    def test_true_with_groq_key(self, env_file):
        env_file.write_text("GROQ_API_KEY=gsk-test\n")
        assert is_configured() is True

    def test_false_with_only_non_llm_keys(self, env_file):
        env_file.write_text("SERPER_API_KEY=serp-key\nJINA_API_KEY=jina-key\n")
        assert is_configured() is False
