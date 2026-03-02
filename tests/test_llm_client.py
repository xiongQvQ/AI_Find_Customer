"""
Tests for core/llm_client.py

These tests are fully offline — they mock litellm.completion so no real API
calls are made.  Run with:
    python -m pytest tests/test_llm_client.py -v
"""

import os
import sys
import json
import types
from unittest.mock import MagicMock, patch

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# Helper to build a fake litellm response object
# ---------------------------------------------------------------------------

def _make_response(text: str):
    msg = MagicMock()
    msg.content = text
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


# ---------------------------------------------------------------------------
# get_llm_model / is_llm_available
# ---------------------------------------------------------------------------

class TestGetLlmModel:
    def test_returns_empty_when_unset(self, monkeypatch):
        monkeypatch.delenv("LLM_MODEL", raising=False)
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        assert lc.get_llm_model() == ""

    def test_returns_model_when_set(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "openai/gpt-4o-mini")
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        assert lc.get_llm_model() == "openai/gpt-4o-mini"

    def test_strips_whitespace(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "  deepseek/deepseek-chat  ")
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        assert lc.get_llm_model() == "deepseek/deepseek-chat"


class TestIsLlmAvailable:
    def test_false_when_model_empty(self, monkeypatch):
        monkeypatch.delenv("LLM_MODEL", raising=False)
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        assert lc.is_llm_available() is False

    def test_false_when_model_set_but_no_key(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "openai/gpt-4o-mini")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        assert lc.is_llm_available() is False

    def test_true_when_model_and_key_present(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "openai/gpt-4o-mini")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        assert lc.is_llm_available() is True

    def test_true_deepseek(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "deepseek/deepseek-chat")
        monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-test")
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        assert lc.is_llm_available() is True

    def test_true_zhipuai(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "zhipuai/glm-4-flash")
        monkeypatch.setenv("ZHIPUAI_API_KEY", "glm-test")
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        assert lc.is_llm_available() is True

    def test_true_minimax(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "minimax/abab6.5s-chat")
        monkeypatch.setenv("MINIMAX_API_KEY", "mm-test")
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        assert lc.is_llm_available() is True

    def test_true_volcengine(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "volcengine/doubao-1-5-pro-256k-250115")
        monkeypatch.setenv("VOLCENGINE_API_KEY", "volc-test")
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        assert lc.is_llm_available() is True

    def test_true_openrouter(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "openrouter/google/gemma-3-27b-it:free")
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-test")
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        assert lc.is_llm_available() is True

    def test_true_xai_grok(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "xai/grok-3-mini-beta")
        monkeypatch.setenv("XAI_API_KEY", "xai-test")
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        assert lc.is_llm_available() is True

    def test_true_anthropic(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "anthropic/claude-3-haiku-20240307")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "ant-test")
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        assert lc.is_llm_available() is True

    def test_true_google(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "gemini/gemini-1.5-flash")
        monkeypatch.setenv("GOOGLE_API_KEY", "goog-test")
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        assert lc.is_llm_available() is True


# ---------------------------------------------------------------------------
# call_llm
# ---------------------------------------------------------------------------

class TestCallLlm:
    def test_raises_when_no_model(self, monkeypatch):
        monkeypatch.delenv("LLM_MODEL", raising=False)
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        try:
            lc.call_llm("sys", "user")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "LLM_MODEL" in str(e)

    def test_returns_text_on_success(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "openai/gpt-4o-mini")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        from importlib import reload
        import core.llm_client as lc
        reload(lc)

        with patch("litellm.completion", return_value=_make_response("hello world")) as mock_comp:
            result = lc.call_llm("system prompt", "user message")
        assert result == "hello world"
        mock_comp.assert_called_once()
        call_kwargs = mock_comp.call_args[1]
        assert call_kwargs["model"] == "openai/gpt-4o-mini"
        assert call_kwargs["temperature"] == 0.6

    def test_passes_custom_temperature_and_max_tokens(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "deepseek/deepseek-chat")
        monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-test")
        from importlib import reload
        import core.llm_client as lc
        reload(lc)

        with patch("litellm.completion", return_value=_make_response("ok")) as mock_comp:
            lc.call_llm("s", "u", temperature=0.1, max_tokens=512)
        kw = mock_comp.call_args[1]
        assert kw["temperature"] == 0.1
        assert kw["max_tokens"] == 512

    def test_volcengine_adds_api_base(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "volcengine/doubao-1-5-pro-256k-250115")
        monkeypatch.setenv("VOLCENGINE_API_KEY", "volc-test")
        monkeypatch.setenv("VOLCENGINE_API_BASE", "https://ark.cn-beijing.volces.com/api/v3")
        from importlib import reload
        import core.llm_client as lc
        reload(lc)

        with patch("litellm.completion", return_value=_make_response("ok")) as mock_comp:
            lc.call_llm("s", "u")
        kw = mock_comp.call_args[1]
        assert "api_base" in kw
        assert "volces.com" in kw["api_base"]

    def test_openrouter_adds_headers(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "openrouter/google/gemma-3-27b-it:free")
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-test")
        from importlib import reload
        import core.llm_client as lc
        reload(lc)

        with patch("litellm.completion", return_value=_make_response("ok")) as mock_comp:
            lc.call_llm("s", "u")
        kw = mock_comp.call_args[1]
        assert "headers" in kw
        assert "HTTP-Referer" in kw["headers"]

    def test_raises_runtime_on_litellm_error(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "openai/gpt-4o-mini")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        from importlib import reload
        import core.llm_client as lc
        reload(lc)

        with patch("litellm.completion", side_effect=Exception("network error")):
            try:
                lc.call_llm("s", "u")
                assert False, "Should have raised RuntimeError"
            except RuntimeError as e:
                assert "LLM call failed" in str(e)


# ---------------------------------------------------------------------------
# parse_json_response
# ---------------------------------------------------------------------------

class TestParseJsonResponse:
    def setup_method(self):
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        self.parse = lc.parse_json_response

    def test_plain_json_object(self):
        raw = '{"keywords": ["foo", "bar"]}'
        result = self.parse(raw)
        assert result == {"keywords": ["foo", "bar"]}

    def test_plain_json_array(self):
        raw = '["foo", "bar", "baz"]'
        result = self.parse(raw)
        assert result == ["foo", "bar", "baz"]

    def test_markdown_fenced_json(self):
        raw = '```json\n{"key": "value"}\n```'
        result = self.parse(raw)
        assert result == {"key": "value"}

    def test_markdown_fenced_no_lang(self):
        raw = '```\n["a", "b"]\n```'
        result = self.parse(raw)
        assert result == ["a", "b"]

    def test_json_embedded_in_text(self):
        raw = 'Here are your keywords:\n{"keywords": ["x"]}\nEnd.'
        result = self.parse(raw)
        assert result == {"keywords": ["x"]}

    def test_empty_string_returns_none(self):
        assert self.parse("") is None

    def test_none_returns_none(self):
        assert self.parse(None) is None

    def test_invalid_json_returns_none(self):
        assert self.parse("not json at all, no braces") is None

    def test_nested_object(self):
        raw = '{"a": {"b": [1, 2, 3]}}'
        result = self.parse(raw)
        assert result["a"]["b"] == [1, 2, 3]


# ---------------------------------------------------------------------------
# Integration: keyword_generator uses core/llm_client
# ---------------------------------------------------------------------------

class TestKeywordGeneratorUsesLlmClient:
    def test_generate_keywords_calls_call_llm(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "openai/gpt-4o-mini")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        fake_keywords = ["solar inverter distributor", "PV module importer Germany"]
        fake_raw = json.dumps(fake_keywords)

        with patch("core.llm_client.call_llm", return_value=fake_raw) as mock_call:
            from importlib import reload
            import keyword_generator as kg
            reload(kg)
            result = kg.generate_keywords("solar inverter", ["Germany"], count=2)

        mock_call.assert_called_once()
        assert len(result) == 2
        assert "solar inverter distributor" in result

    def test_generate_keywords_deduplicates(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "openai/gpt-4o-mini")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        duped = json.dumps(["keyword one", "keyword one", "keyword two"])
        with patch("core.llm_client.call_llm", return_value=duped):
            from importlib import reload
            import keyword_generator as kg
            reload(kg)
            result = kg.generate_keywords("pump", ["USA"], count=3)

        assert result.count("keyword one") == 1
        assert len(result) == 2


# ---------------------------------------------------------------------------
# Integration: UnifiedLLMProcessor uses core/llm_client
# ---------------------------------------------------------------------------

class TestUnifiedLLMProcessor:
    def test_available_flag_reflects_is_llm_available(self, monkeypatch):
        monkeypatch.delenv("LLM_MODEL", raising=False)
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        import extract_contact_info as eci
        reload(eci)

        proc = eci.UnifiedLLMProcessor()
        assert proc.available is False

    def test_extract_returns_empty_when_unavailable(self, monkeypatch):
        monkeypatch.delenv("LLM_MODEL", raising=False)
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        import extract_contact_info as eci
        reload(eci)

        proc = eci.UnifiedLLMProcessor()
        result = proc.extract_contact_info({"main_content": "<html>hello</html>"}, "http://example.com")
        assert result["website"] == "http://example.com"
        assert result["email"] == ""

    def test_extract_calls_call_llm_when_available(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "openai/gpt-4o-mini")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        import extract_contact_info as eci
        reload(eci)

        fake_result = {
            "company_name": "Acme Corp",
            "email": "info@acme.com",
            "phone": "+1-800-000",
            "address": "123 Main St",
            "linkedin": "",
            "twitter": "",
            "facebook": "",
            "instagram": "",
        }
        with patch("extract_contact_info.call_llm", return_value=json.dumps(fake_result)):
            proc = eci.UnifiedLLMProcessor()
            result = proc.extract_contact_info({"main_content": "<html>Acme Corp</html>"}, "http://acme.com")

        assert result["email"] == "info@acme.com"
        assert result["website"] == "http://acme.com"

    def test_truncate_content(self, monkeypatch):
        monkeypatch.delenv("LLM_MODEL", raising=False)
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        import extract_contact_info as eci
        reload(eci)

        proc = eci.UnifiedLLMProcessor()
        long_text = "x" * 40000
        truncated = proc._truncate_content(long_text, max_length=32000)
        assert len(truncated) <= 32000 + 50  # allow for truncation marker
        assert "[content truncated]" in truncated

    def test_truncate_short_content_unchanged(self, monkeypatch):
        monkeypatch.delenv("LLM_MODEL", raising=False)
        from importlib import reload
        import core.llm_client as lc
        reload(lc)
        import extract_contact_info as eci
        reload(eci)

        proc = eci.UnifiedLLMProcessor()
        short = "hello world"
        assert proc._truncate_content(short) == short
