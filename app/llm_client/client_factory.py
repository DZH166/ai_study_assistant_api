# -*- coding: utf-8 -*-

from app.core.config import get_settings
from app.llm_client.llm_error_handler import LLMClientError, should_use_mock_fallback
from app.llm_client.mock_client import call_mock_llm
from app.llm_client.openai_compatible_client import call_openai_compatible_llm
from app.schemas.chat import ChatMessage


def call_llm(messages: list[ChatMessage], temperature: float) -> dict:
    """
    统一的大模型调用入口。

    根据 .env 配置决定当前使用 mock 还是真实 OpenAI-compatible 模型。
    """
    settings = get_settings()

    if settings.use_mock_llm:
        return call_mock_llm(
            messages=messages,
            temperature=temperature,
            model_name=settings.llm_model_name,
        )

    try:
        return call_openai_compatible_llm(
            messages=messages,
            temperature=temperature,
            settings=settings,
        )
    except LLMClientError as exc:
        if not should_use_mock_fallback(
            error=exc,
            app_env=settings.app_env,
            enable_mock_fallback=settings.enable_mock_fallback,
        ):
            raise

        fallback_result = call_mock_llm(
            messages=messages,
            temperature=temperature,
            model_name=settings.llm_model_name,
        )
        fallback_result["model"] = f"fallback:{fallback_result['model']}"
        fallback_result["fallback_used"] = True
        fallback_result["fallback_reason"] = exc.code
        return fallback_result
