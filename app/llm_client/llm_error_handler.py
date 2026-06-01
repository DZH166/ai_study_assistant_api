# -*- coding: utf-8 -*-

from dataclasses import dataclass

import httpx


FALLBACK_ALLOWED_CODES = {
    "LLM_RATE_LIMITED",
    "LLM_TIMEOUT",
    "LLM_CONNECTION_ERROR",
    "LLM_PROVIDER_ERROR",
}

FALLBACK_BLOCKED_CODES = {
    "LLM_AUTH_FAILED",
    "LLM_RESOURCE_NOT_FOUND",
    "LLM_RESPONSE_FORMAT_ERROR",
    "LLM_HTTP_ERROR",
}


@dataclass
class LLMClientError(Exception):
    """
    统一的大模型调用异常。

    这一层的目标不是把供应商原始错误完整暴露给前端，
    而是把错误转换成后端可控、前端可理解的格式。
    """

    message: str
    code: str
    status_code: int = 502
    detail: str | None = None


def map_http_status_error(exc: httpx.HTTPStatusError) -> LLMClientError:
    """
    把模型供应商返回的 HTTP 状态码转换成业务可理解的 LLM 错误。

    注意：
    这里的 status_code 是我们的后端接口对前端返回的状态码，
    不一定要和供应商原始状态码完全一致。
    """
    upstream_status = exc.response.status_code

    if upstream_status == 401:
        return LLMClientError(
            message="模型服务鉴权失败，请检查 API Key 配置",
            code="LLM_AUTH_FAILED",
            status_code=502,
            detail="Upstream model provider returned 401.",
        )

    if upstream_status == 404:
        return LLMClientError(
            message="模型服务地址或模型名称不存在，请检查 base_url 和 model 配置",
            code="LLM_RESOURCE_NOT_FOUND",
            status_code=502,
            detail="Upstream model provider returned 404.",
        )

    if upstream_status == 429:
        return LLMClientError(
            message="模型服务请求过于频繁，请稍后再试",
            code="LLM_RATE_LIMITED",
            status_code=503,
            detail="Upstream model provider returned 429.",
        )

    if 500 <= upstream_status < 600:
        return LLMClientError(
            message="模型服务暂时不可用，请稍后重试",
            code="LLM_PROVIDER_ERROR",
            status_code=502,
            detail=f"Upstream model provider returned {upstream_status}.",
        )

    return LLMClientError(
        message="模型服务调用失败",
        code="LLM_HTTP_ERROR",
        status_code=502,
        detail=f"Upstream model provider returned {upstream_status}.",
    )


def map_request_error(exc: httpx.RequestError) -> LLMClientError:
    """
    把网络层异常转换成统一 LLM 错误。

    RequestError 通常表示还没拿到正常响应，
    例如超时、DNS 问题、连接失败等。
    """
    if isinstance(exc, httpx.TimeoutException):
        return LLMClientError(
            message="模型响应超时，请稍后重试",
            code="LLM_TIMEOUT",
            status_code=504,
            detail="Request to model provider timed out.",
        )

    return LLMClientError(
        message="无法连接模型服务，请稍后重试",
        code="LLM_CONNECTION_ERROR",
        status_code=502,
        detail="Request to model provider failed before receiving a response.",
    )


def map_response_parse_error(exc: Exception) -> LLMClientError:
    """
    把响应解析失败转换成统一 LLM 错误。

    这类错误通常表示供应商返回结构和我们预期不一致。
    """
    return LLMClientError(
        message="模型返回格式异常，请稍后重试",
        code="LLM_RESPONSE_FORMAT_ERROR",
        status_code=502,
        detail=str(exc),
    )


def should_use_mock_fallback(
    error: LLMClientError,
    app_env: str,
    enable_mock_fallback: bool,
) -> bool:
    """
    判断真实模型失败后，是否允许临时降级到 mock 模型。

    企业判断：
    - 鉴权失败、模型名错误、响应格式异常，通常代表配置或代码有问题，不能假装成功。
    - 限流、超时、连接失败、供应商短暂 5xx，通常是临时可恢复问题，开发环境可以降级演示。
    - 生产环境默认不降级到 mock，避免给用户返回“看起来成功但其实是假的”结果。
    """
    if not enable_mock_fallback:
        return False

    if app_env.strip().lower() == "prod":
        return False

    if error.code in FALLBACK_BLOCKED_CODES:
        return False

    return error.code in FALLBACK_ALLOWED_CODES
