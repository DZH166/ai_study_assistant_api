# -*- coding: utf-8 -*-

import httpx

from app.core.config import Settings
from app.llm_client.llm_error_handler import (
    LLMClientError,
    map_http_status_error,
    map_request_error,
    map_response_parse_error,
)
from app.schemas.chat import ChatMessage


def _build_payload(
    messages: list[ChatMessage],
    temperature: float,
    settings: Settings,
) -> dict:
    """
    构造 OpenAI-compatible 请求体。

    业务层传进来的是 ChatMessage 对象列表；
    外部 HTTP API 需要的是可以被 JSON 序列化的 dict 列表。
    """
    return {
        "model": settings.llm_model_name,
        "messages": [
            {"role": message.role, "content": message.content}
            for message in messages
        ],
        "temperature": temperature,
    }


def _build_headers(settings: Settings) -> dict:
    """
    构造请求头。

    Authorization 用于证明你有权限调用模型；
    Content-Type 告诉对方这次请求体是 JSON。
    """
    return {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }


def _build_chat_completions_url(base_url: str) -> str:
    """
    拼接聊天补全接口地址。

    兼容用户在 .env 中写：
    - https://api.example.com/v1
    - https://api.example.com/v1/
    """
    return f"{base_url.rstrip('/')}/chat/completions"


def _extract_answer(response_data: dict) -> str:
    """
    从模型供应商返回的完整响应中提取 answer。

    OpenAI-compatible 常见结构：
    choices[0].message.content 才是真正要展示给用户的文本。
    """
    try:
        return response_data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("模型返回格式异常，无法提取 answer") from exc


def call_openai_compatible_llm(
    messages: list[ChatMessage],
    temperature: float,
    settings: Settings,
) -> dict:
    """
    调用 OpenAI-compatible 聊天模型。

    这一层只负责模型供应商通信：
    1. 拼请求头
    2. 拼请求体
    3. 发送 HTTP 请求
    4. 解析供应商响应
    5. 返回 service 层需要的统一结构
    """
    if not settings.llm_api_key:
        raise LLMClientError(
            message="调用真实模型前必须配置 API Key",
            code="LLM_API_KEY_MISSING",
            status_code=500,
            detail="LLM_API_KEY is empty while USE_MOCK_LLM=false.",
        )

    url = _build_chat_completions_url(settings.llm_base_url)
    headers = _build_headers(settings)
    payload = _build_payload(
        messages=messages,
        temperature=temperature,
        settings=settings,
    )

    try:
        response = httpx.post(
            url=url,
            headers=headers,
            json=payload,
            timeout=settings.llm_timeout,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise map_http_status_error(exc) from exc
    except httpx.RequestError as exc:
        raise map_request_error(exc) from exc

    try:
        response_data = response.json()
        answer = _extract_answer(response_data)
    except Exception as exc:
        raise map_response_parse_error(exc) from exc

    return {
        "answer": answer,
        "model": response_data.get("model", settings.llm_model_name),
        "usage": response_data.get("usage", {}),
    }
