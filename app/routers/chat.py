# -*- coding: utf-8 -*-

import json
from collections.abc import Iterator

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from app.llm_client.llm_error_handler import LLMClientError
from app.schemas.chat import ChatRequest
from app.services.chat_service import chat_with_ai, stream_chat_events
from app.utils.response import error_response, success_response


router = APIRouter(prefix="/chat", tags=["chat"])


def format_sse_event(event: str, data: dict) -> str:
    """
    把业务事件包装成 SSE 文本格式。

    SSE 基本格式：
    event: 事件名
    data: JSON 字符串

    注意最后必须有一个空行，浏览器才知道这一条事件结束了。
    """
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


def format_chat_stream(events: Iterator[dict]) -> Iterator[str]:
    """
    把 service 层产生的事件流转换成浏览器可识别的 SSE 字符串。
    """
    for item in events:
        yield format_sse_event(event=item["event"], data=item["data"])


@router.post("")
def chat(request: ChatRequest):
    """
    聊天接口入口。

    router 层只做三件事：
    1. 接收 HTTP 请求
    2. 把请求交给 service
    3. 把 service 的结果包装后返回
    """
    try:
        result = chat_with_ai(request)
    except LLMClientError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(
                message=exc.message,
                code=exc.code,
                detail=exc.detail,
            ),
        )

    # Pydantic v2 用 model_dump；如果遇到旧版本 Pydantic，则回退到 dict。
    data = result.model_dump() if hasattr(result, "model_dump") else result.dict()
    return success_response(message="聊天成功", data=data)


@router.post("/stream")
def chat_stream(request: ChatRequest):
    """
    聊天流式接口入口。

    和普通 /chat 的区别：
    - /chat 等完整答案生成后一次性返回 JSON
    - /chat/stream 用 SSE 一段一段返回内容
    """
    events = stream_chat_events(request)
    return StreamingResponse(
        format_chat_stream(events),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
