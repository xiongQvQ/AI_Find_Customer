"""Tests for tools/react_runner.py — JSON parsing, field validation, message trimming."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from config.settings import Settings
from tools.react_runner import (
    _acompletion_with_rpm_limit,
    _clean_markdown_fences,
    _has_required_fields,
    _trim_messages,
    _try_parse_json,
)


class TestCleanMarkdownFences:
    def test_no_fences(self):
        assert _clean_markdown_fences('{"a": 1}') == '{"a": 1}'

    def test_json_fences(self):
        text = '```json\n{"a": 1}\n```'
        assert _clean_markdown_fences(text) == '{"a": 1}'

    def test_plain_fences(self):
        text = '```\n{"a": 1}\n```'
        assert _clean_markdown_fences(text) == '{"a": 1}'

    def test_trailing_whitespace(self):
        text = '  ```json\n{"a": 1}\n```  '
        assert _clean_markdown_fences(text) == '{"a": 1}'


class TestTryParseJson:
    def test_valid_json_object(self):
        result = _try_parse_json('{"name": "test", "value": 42}')
        assert result == {"name": "test", "value": 42}

    def test_valid_json_array(self):
        result = _try_parse_json('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_markdown_fenced_json(self):
        text = '```json\n{"name": "test"}\n```'
        result = _try_parse_json(text)
        assert result == {"name": "test"}

    def test_json_with_surrounding_prose(self):
        text = 'Here is the result:\n{"name": "test", "score": 0.5}\nDone!'
        result = _try_parse_json(text)
        assert result == {"name": "test", "score": 0.5}

    def test_invalid_json(self):
        assert _try_parse_json("This is not JSON at all") is None

    def test_empty_string(self):
        assert _try_parse_json("") is None

    def test_none_like(self):
        assert _try_parse_json("   ") is None

    def test_partial_json(self):
        # Malformed JSON should return None
        assert _try_parse_json('{"name": "test", ') is None

    def test_complex_nested_json(self):
        data = {
            "is_valid_lead": True,
            "company_name": "Acme Corp",
            "emails": ["info@acme.com"],
            "social_media": {"linkedin": "https://linkedin.com/company/acme"},
            "match_score": 0.85,
        }
        result = _try_parse_json(json.dumps(data))
        assert result == data

    def test_json_with_thinking_prefix(self):
        """Models sometimes output thinking before JSON."""
        text = 'Let me analyze this...\n\n{"is_valid_lead": true, "company_name": "Test"}'
        result = _try_parse_json(text)
        assert result is not None
        assert result["company_name"] == "Test"


class TestHasRequiredFields:
    def test_all_fields_present(self):
        data = {"name": "test", "email": "a@b.com", "score": 0.5}
        assert _has_required_fields(data, ["name", "email", "score"]) is True

    def test_missing_field(self):
        data = {"name": "test", "score": 0.5}
        assert _has_required_fields(data, ["name", "email", "score"]) is False

    def test_empty_requirements(self):
        assert _has_required_fields({"any": "data"}, []) is True

    def test_none_parsed(self):
        assert _has_required_fields(None, ["name"]) is True  # Can't check non-dict

    def test_list_parsed(self):
        assert _has_required_fields([1, 2, 3], ["name"]) is True  # Accept as-is for lists

    def test_field_with_none_value_still_present(self):
        """Field exists but has None value — should still pass (key exists)."""
        data = {"name": None, "email": "a@b.com"}
        assert _has_required_fields(data, ["name", "email"]) is True


class TestTrimMessages:
    def test_short_list_unchanged(self):
        msgs = [{"role": "system"}, {"role": "user"}, {"role": "assistant"}]
        result = _trim_messages(msgs, keep_last=10)
        assert result == msgs

    def test_trims_middle_messages(self):
        msgs = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "usr"},
        ]
        # Add 20 more messages
        for i in range(20):
            msgs.append({"role": "assistant", "content": f"msg-{i}"})

        result = _trim_messages(msgs, keep_last=5)
        # Should keep system + user + last 5
        assert len(result) == 7
        assert result[0]["content"] == "sys"
        assert result[1]["content"] == "usr"
        assert result[2]["content"] == "msg-15"
        assert result[-1]["content"] == "msg-19"

    def test_exactly_at_limit(self):
        msgs = [{"role": "system"}, {"role": "user"}]
        for i in range(10):
            msgs.append({"role": "assistant", "content": f"msg-{i}"})

        result = _trim_messages(msgs, keep_last=10)
        assert len(result) == 12  # No trimming needed


class TestRPMControl:
    @pytest.mark.asyncio
    async def test_reasoning_calls_apply_rpm_limiter(self):
        settings = Settings(
            reasoning_requests_per_minute=9,
            llm_requests_per_minute=0,
        )
        limiter = AsyncMock()
        mock_resp = SimpleNamespace(choices=[])

        with patch("tools.react_runner.get_llm_rate_limiter", return_value=limiter) as mock_get:
            with patch("tools.react_runner.litellm.acompletion", new_callable=AsyncMock, return_value=mock_resp) as mock_call:
                result = await _acompletion_with_rpm_limit(settings, model="gpt-4o", messages=[])

        assert result is mock_resp
        mock_get.assert_called_once_with("reasoning", 9)
        limiter.acquire.assert_awaited_once()
        mock_call.assert_awaited_once()
