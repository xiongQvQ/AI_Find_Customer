"""Tests for tools/llm_client.py — mock litellm.acompletion for multi-provider LLM."""

import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from config.settings import Settings
from tools.llm_client import LLMTool, _inject_api_keys
from tools.llm_errors import format_llm_error


def _make_settings(**overrides) -> Settings:
    defaults = {
        "openai_api_key": "sk-test",
        "anthropic_api_key": "ant-test",
        "llm_model": "gpt-4o-mini",
        "llm_temperature": 0.3,
        "llm_max_tokens": 4096,
        "llm_requests_per_minute": 0,
        "reasoning_model": "gpt-4o",
        "reasoning_temperature": 0.2,
        "reasoning_max_tokens": 4096,
        "reasoning_requests_per_minute": 0,
        "email_llm_model": "",
        "email_reasoning_model": "",
        "email_llm_requests_per_minute": 0,
        "email_reasoning_requests_per_minute": 0,
    }
    defaults.update(overrides)
    return Settings(**defaults)


def _mock_completion(content: str) -> SimpleNamespace:
    """Build a fake litellm response object."""
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
    )


class TestLLMToolProperties:
    def test_default_model(self):
        tool = LLMTool(settings=_make_settings())
        assert tool.model == "gpt-4o-mini"

    def test_custom_model(self):
        tool = LLMTool(settings=_make_settings(llm_model="anthropic/claude-3-5-sonnet-20241022"))
        assert tool.model == "anthropic/claude-3-5-sonnet-20241022"

    def test_groq_model(self):
        tool = LLMTool(settings=_make_settings(llm_model="groq/llama-3.3-70b-versatile"))
        assert tool.model == "groq/llama-3.3-70b-versatile"

    def test_reasoning_model(self):
        tool = LLMTool(model_type="reasoning", settings=_make_settings())
        assert tool.model == "gpt-4o"

    def test_reasoning_model_custom(self):
        tool = LLMTool(model_type="reasoning", settings=_make_settings(reasoning_model="anthropic/claude-3-5-sonnet-20241022"))
        assert tool.model == "anthropic/claude-3-5-sonnet-20241022"

    def test_reasoning_temperature(self):
        tool = LLMTool(model_type="reasoning", settings=_make_settings(reasoning_temperature=0.1))
        assert tool._default_temperature == 0.1

    def test_email_model_falls_back_to_default(self):
        tool = LLMTool(model_type="email", settings=_make_settings())
        assert tool.model == "gpt-4o-mini"

    def test_email_model_uses_dedicated_model(self):
        tool = LLMTool(model_type="email", settings=_make_settings(email_llm_model="openrouter/google/gemini-flash-1.5"))
        assert tool.model == "openrouter/google/gemini-flash-1.5"

    def test_email_reasoning_model_uses_dedicated_model(self):
        tool = LLMTool(model_type="email_reasoning", settings=_make_settings(email_reasoning_model="openrouter/deepseek/deepseek-r1"))
        assert tool.model == "openrouter/deepseek/deepseek-r1"

    def test_default_temperature(self):
        tool = LLMTool(settings=_make_settings(llm_temperature=0.5))
        assert tool._default_temperature == 0.5


class TestLLMToolGenerate:
    @pytest.mark.asyncio
    async def test_generate_basic(self):
        tool = LLMTool(settings=_make_settings())
        mock_resp = _mock_completion("Hello from GPT")

        with patch("tools.llm_client.litellm.acompletion", new_callable=AsyncMock, return_value=mock_resp) as mock_call:
            result = await tool.generate("Say hello")

        assert result == "Hello from GPT"
        mock_call.assert_called_once()
        kwargs = mock_call.call_args.kwargs
        assert kwargs["model"] == "gpt-4o-mini"
        assert kwargs["messages"] == [{"role": "user", "content": "Say hello"}]

    @pytest.mark.asyncio
    async def test_generate_with_system(self):
        tool = LLMTool(settings=_make_settings())
        mock_resp = _mock_completion("ok")

        with patch("tools.llm_client.litellm.acompletion", new_callable=AsyncMock, return_value=mock_resp) as mock_call:
            await tool.generate("user msg", system="system msg")

        kwargs = mock_call.call_args.kwargs
        assert kwargs["messages"][0] == {"role": "system", "content": "system msg"}
        assert kwargs["messages"][1] == {"role": "user", "content": "user msg"}

    @pytest.mark.asyncio
    async def test_generate_temperature_override(self):
        tool = LLMTool(settings=_make_settings())
        mock_resp = _mock_completion("ok")

        with patch("tools.llm_client.litellm.acompletion", new_callable=AsyncMock, return_value=mock_resp) as mock_call:
            await tool.generate("test", temperature=0.9)

        assert mock_call.call_args.kwargs["temperature"] == 0.9

    @pytest.mark.asyncio
    async def test_generate_max_tokens_override(self):
        tool = LLMTool(settings=_make_settings())
        mock_resp = _mock_completion("ok")

        with patch("tools.llm_client.litellm.acompletion", new_callable=AsyncMock, return_value=mock_resp) as mock_call:
            await tool.generate("test", max_tokens=1024)

        assert mock_call.call_args.kwargs["max_tokens"] == 1024

    @pytest.mark.asyncio
    async def test_generate_json_mode(self):
        tool = LLMTool(settings=_make_settings())
        mock_resp = _mock_completion('{"key": "val"}')

        with patch("tools.llm_client.litellm.acompletion", new_callable=AsyncMock, return_value=mock_resp) as mock_call:
            result = await tool.generate("test", response_format={"type": "json_object"})

        assert result == '{"key": "val"}'
        assert mock_call.call_args.kwargs["response_format"] == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_generate_json_mode_skips_response_format_for_zai(self):
        tool = LLMTool(settings=_make_settings(llm_model="zai/glm-4.7"))
        mock_resp = _mock_completion('{"key": "val"}')

        with patch("tools.llm_client.litellm.acompletion", new_callable=AsyncMock, return_value=mock_resp) as mock_call:
            result = await tool.generate("test", response_format={"type": "json_object"})

        assert result == '{"key": "val"}'
        assert "response_format" not in mock_call.call_args.kwargs

    @pytest.mark.asyncio
    async def test_generate_uses_default_temperature(self):
        tool = LLMTool(settings=_make_settings(llm_temperature=0.7))
        mock_resp = _mock_completion("ok")

        with patch("tools.llm_client.litellm.acompletion", new_callable=AsyncMock, return_value=mock_resp) as mock_call:
            await tool.generate("test")

        assert mock_call.call_args.kwargs["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_generate_reasoning_model(self):
        """Verify reasoning model_type uses reasoning_model and reasoning_temperature."""
        tool = LLMTool(model_type="reasoning", settings=_make_settings(
            reasoning_model="gpt-4o", reasoning_temperature=0.2,
        ))
        mock_resp = _mock_completion("ok")

        with patch("tools.llm_client.litellm.acompletion", new_callable=AsyncMock, return_value=mock_resp) as mock_call:
            await tool.generate("test")

        assert mock_call.call_args.kwargs["model"] == "gpt-4o"
        assert mock_call.call_args.kwargs["temperature"] == 0.2

    @pytest.mark.asyncio
    async def test_generate_different_models(self):
        """Verify model name is passed through to litellm."""
        for model_name in [
            "gpt-4o-mini",
            "anthropic/claude-3-5-sonnet-20241022",
            "openrouter/google/gemini-pro",
            "groq/llama-3.3-70b-versatile",
            "zai/glm-4.7",
            "moonshot/moonshot-v1-128k",
            "minimax/MiniMax-Text-01",
        ]:
            tool = LLMTool(settings=_make_settings(llm_model=model_name))
            mock_resp = _mock_completion("ok")

            with patch("tools.llm_client.litellm.acompletion", new_callable=AsyncMock, return_value=mock_resp) as mock_call:
                await tool.generate("test")

            assert mock_call.call_args.kwargs["model"] == model_name

    @pytest.mark.asyncio
    async def test_generate_applies_rpm_limiter(self):
        tool = LLMTool(settings=_make_settings(llm_requests_per_minute=12))
        mock_resp = _mock_completion("ok")
        limiter = AsyncMock()

        with patch("tools.llm_client.get_llm_rate_limiter", return_value=limiter) as mock_get:
            with patch("tools.llm_client.litellm.acompletion", new_callable=AsyncMock, return_value=mock_resp):
                await tool.generate("test")

        mock_get.assert_called_once_with("default", 12)
        limiter.acquire.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_generate_email_model_applies_dedicated_rpm_limiter(self):
        tool = LLMTool(model_type="email", settings=_make_settings(email_llm_requests_per_minute=7))
        mock_resp = _mock_completion("ok")
        limiter = AsyncMock()

        with patch("tools.llm_client.get_llm_rate_limiter", return_value=limiter) as mock_get:
            with patch("tools.llm_client.litellm.acompletion", new_callable=AsyncMock, return_value=mock_resp):
                await tool.generate("test")

        mock_get.assert_called_once_with("email", 7)
        limiter.acquire.assert_awaited_once()


class TestLLMToolErrors:
    @pytest.mark.asyncio
    async def test_litellm_error_propagates(self):
        tool = LLMTool(settings=_make_settings())

        with patch("tools.llm_client.litellm.acompletion", new_callable=AsyncMock, side_effect=Exception("API error")):
            with pytest.raises(RuntimeError, match="API error"):
                await tool.generate("test")

    @pytest.mark.asyncio
    async def test_minimax_insufficient_balance_is_reworded(self):
        tool = LLMTool(settings=_make_settings())
        upstream = (
            'litellm.APIConnectionError: MinimaxException - '
            '{"type":"error","error":{"type":"insufficient_balance_error",'
            '"message":"insufficient balance (1008)","http_code":"429"}}'
        )

        with patch("tools.llm_client.litellm.acompletion", new_callable=AsyncMock, side_effect=Exception(upstream)):
            with pytest.raises(RuntimeError, match="账户余额不足"):
                await tool.generate("test")


class TestFormatLLMError:
    def test_formats_insufficient_balance(self):
        msg = format_llm_error(Exception(
            'MinimaxException - {"error":{"type":"insufficient_balance_error","message":"insufficient balance (1008)","http_code":"429"}}'
        ))
        assert "账户余额不足" in msg
        assert "MiniMax API 调用失败" in msg

    def test_formats_generic_429(self):
        msg = format_llm_error(Exception('provider error {"http_code":"429"}'))
        assert "上游返回 429" in msg


class TestInjectApiKeys:
    def test_injects_keys_into_env(self):
        settings = _make_settings(
            openai_api_key="sk-openai",
            anthropic_api_key="sk-anthropic",
            openrouter_api_key="sk-openrouter",
            groq_api_key="sk-groq",
            zai_api_key="sk-zhipu",
            moonshot_api_key="sk-moonshot",
            minimax_api_key="sk-minimax",
            minimax_api_base="https://api.minimax.io/v1",
        )
        # Clear env vars first
        env_keys = [
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY",
            "GROQ_API_KEY", "ZAI_API_KEY", "MOONSHOT_API_KEY",
            "MINIMAX_API_KEY", "MINIMAX_API_BASE",
        ]
        saved = {}
        for k in env_keys:
            saved[k] = os.environ.pop(k, None)

        try:
            _inject_api_keys(settings)
            assert os.environ["OPENAI_API_KEY"] == "sk-openai"
            assert os.environ["ANTHROPIC_API_KEY"] == "sk-anthropic"
            assert os.environ["OPENROUTER_API_KEY"] == "sk-openrouter"
            assert os.environ["GROQ_API_KEY"] == "sk-groq"
            assert os.environ["ZAI_API_KEY"] == "sk-zhipu"
            assert os.environ["MOONSHOT_API_KEY"] == "sk-moonshot"
            assert os.environ["MINIMAX_API_KEY"] == "sk-minimax"
            assert os.environ["MINIMAX_API_BASE"] == "https://api.minimax.io/v1"
        finally:
            # Restore original env
            for k in env_keys:
                if saved[k] is not None:
                    os.environ[k] = saved[k]
                else:
                    os.environ.pop(k, None)

    def test_overwrites_existing_env_with_current_settings(self):
        settings = _make_settings(openai_api_key="new-key")
        os.environ["OPENAI_API_KEY"] = "existing-key"
        try:
            _inject_api_keys(settings)
            assert os.environ["OPENAI_API_KEY"] == "new-key"
        finally:
            os.environ.pop("OPENAI_API_KEY", None)

    def test_skips_empty_keys(self):
        settings = _make_settings(groq_api_key="")
        os.environ.pop("GROQ_API_KEY", None)
        _inject_api_keys(settings)
        assert "GROQ_API_KEY" not in os.environ

    def test_overwrites_stale_zai_key_for_reasoning_model(self):
        settings = _make_settings(
            reasoning_model="zai/glm-4.7",
            zai_api_key="new-zai-key",
        )
        os.environ["ZAI_API_KEY"] = "stale-zai-key"
        os.environ["ZHIPUAI_API_KEY"] = "stale-zai-key"
        try:
            _inject_api_keys(settings)
            assert os.environ["ZAI_API_KEY"] == "new-zai-key"
            assert os.environ["ZHIPUAI_API_KEY"] == "new-zai-key"
        finally:
            os.environ.pop("ZAI_API_KEY", None)
            os.environ.pop("ZHIPUAI_API_KEY", None)


class TestLLMToolLifecycle:
    @pytest.mark.asyncio
    async def test_close_is_noop(self):
        tool = LLMTool(settings=_make_settings())
        await tool.close()  # Should not raise
