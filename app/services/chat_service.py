# -*- coding: utf-8 -*-

import time
from collections.abc import Iterator

from app.data.conversation_store import (
    ConversationNotFoundError,
    append_message,
    count_messages,
    count_rounds,
    create_conversation,
    get_recent_history,
)
from app.llm_client.client_factory import call_llm
from app.llm_client.llm_error_handler import LLMClientError
from app.prompts.chat_prompts import build_system_prompt
from app.schemas.chat import ChatMessage, ChatRequest, ChatResponse, MessageItem
from app.services.memory_service import (
    MemorySummaryResult,
    build_summary_memory_message,
    refresh_summary_memory,
)


STREAM_CHUNK_SIZE = 12
STREAM_DELAY_SECONDS = 0.05


def convert_history_to_chat_messages(history: list[MessageItem]) -> list[ChatMessage]:
    """
    把后端存储的历史消息转换成大模型需要的 messages 格式。

    存储层只保存 user/assistant，system prompt 每次临时拼接。
    """
    return [
        ChatMessage(role=message.role, content=message.content)
        for message in history
    ]


def build_messages(
    request: ChatRequest,
    history: list[MessageItem],
    memory_summary_result: MemorySummaryResult,
) -> list[ChatMessage]:
    """
    把接口请求体转换成大模型需要的 messages。

    顺序非常重要：
    1. system：先给模型长期规则
    2. summary_memory：再给较早历史的压缩记忆
    3. history：再给最近几轮原文上下文
    4. user：最后放当前问题，让模型回答最新输入
    """
    system_prompt = build_system_prompt(request.current_prompt_scene())
    system_message = ChatMessage(role="system", content=system_prompt)
    summary_messages = (
        [build_summary_memory_message(memory_summary_result.summary_memory)]
        if memory_summary_result.summary_memory
        else []
    )
    history_messages = convert_history_to_chat_messages(history)
    user_message = ChatMessage(role="user", content=request.current_message())

    return [system_message] + summary_messages + history_messages + [user_message]


def prepare_conversation(request: ChatRequest) -> tuple[str, list[MessageItem]]:
    """
    准备会话编号和最近历史。

    第一次请求：创建 conversation_id，历史为空。
    后续请求：根据 conversation_id 读取最近 N 轮历史。
    """
    if request.conversation_id:
        try:
            history = get_recent_history(request.conversation_id)
        except ConversationNotFoundError as exc:
            raise LLMClientError(
                message="会话不存在，请重新开始一次对话",
                code="CONVERSATION_NOT_FOUND",
                status_code=404,
                detail=str(exc),
            ) from exc
        return request.conversation_id, history

    conversation = create_conversation(mode=request.mode)
    return conversation.conversation_id, []


def chat_with_ai(request: ChatRequest) -> ChatResponse:
    """
    聊天业务主流程。

    service 层像导演：它不接 HTTP，不直接关心前端；
    它负责组织 messages、调用模型客户端、整理最终业务结果。
    """
    try:
        current_message = request.current_message()
    except ValueError as exc:
        raise LLMClientError(
            message="用户消息不能为空",
            code="CHAT_MESSAGE_REQUIRED",
            status_code=422,
            detail=str(exc),
        ) from exc

    conversation_id, history = prepare_conversation(request)
    memory_summary_result = refresh_summary_memory(conversation_id)
    messages = build_messages(
        request=request,
        history=history,
        memory_summary_result=memory_summary_result,
    )
    llm_result = call_llm(messages=messages, temperature=request.temperature)

    append_message(conversation_id, role="user", content=current_message)
    append_message(conversation_id, role="assistant", content=llm_result["answer"])

    return ChatResponse(
        answer=llm_result["answer"],
        conversation_id=conversation_id,
        model=llm_result["model"],
        usage=llm_result["usage"],
        messages_count=len(messages),
        history_rounds=count_rounds(conversation_id),
        stored_messages_count=count_messages(conversation_id),
        memory_summary=memory_summary_result.summary_memory,
        memory_summary_used=memory_summary_result.used,
        memory_summary_updated=memory_summary_result.updated,
        memory_summary_failed=memory_summary_result.failed,
        memory_summary_error=memory_summary_result.error,
        fallback_used=llm_result.get("fallback_used", False),
        fallback_reason=llm_result.get("fallback_reason"),
    )


def split_text_for_stream(text: str, chunk_size: int = STREAM_CHUNK_SIZE) -> Iterator[str]:
    """
    把完整文本切成多个小片段，用于模拟流式输出。

    当前 Module26 先把 SSE 接口链路跑通。
    后续接入真实 streaming SDK 时，这里可以替换成供应商返回的 token 流。
    """
    for start in range(0, len(text), chunk_size):
        yield text[start:start + chunk_size]


def stream_chat_events(request: ChatRequest) -> Iterator[dict]:
    """
    生成聊天流式事件。

    事件不是最终 HTTP 文本，router 层会把这些 dict 包装成 SSE 格式。
    """
    try:
        current_message = request.current_message()
        conversation_id, history = prepare_conversation(request)
        memory_summary_result = refresh_summary_memory(conversation_id)
        messages = build_messages(
            request=request,
            history=history,
            memory_summary_result=memory_summary_result,
        )

        yield {
            "event": "start",
            "data": {
                "conversation_id": conversation_id,
                "messages_count": len(messages),
                "memory_summary_used": memory_summary_result.used,
            },
        }

        llm_result = call_llm(messages=messages, temperature=request.temperature)

        yield {
            "event": "metadata",
            "data": {
                "conversation_id": conversation_id,
                "model": llm_result["model"],
                "usage": llm_result["usage"],
                "fallback_used": llm_result.get("fallback_used", False),
                "fallback_reason": llm_result.get("fallback_reason"),
            },
        }

        for chunk in split_text_for_stream(llm_result["answer"]):
            yield {
                "event": "chunk",
                "data": {"content": chunk},
            }
            time.sleep(STREAM_DELAY_SECONDS)

        append_message(conversation_id, role="user", content=current_message)
        append_message(conversation_id, role="assistant", content=llm_result["answer"])

        yield {
            "event": "done",
            "data": {
                "conversation_id": conversation_id,
                "history_rounds": count_rounds(conversation_id),
                "stored_messages_count": count_messages(conversation_id),
                "memory_summary": memory_summary_result.summary_memory,
                "memory_summary_updated": memory_summary_result.updated,
                "memory_summary_failed": memory_summary_result.failed,
                "memory_summary_error": memory_summary_result.error,
            },
        }
    except LLMClientError as exc:
        yield {
            "event": "error",
            "data": {
                "message": exc.message,
                "code": exc.code,
                "status_code": exc.status_code,
                "detail": exc.detail,
            },
        }
    except ValueError as exc:
        yield {
            "event": "error",
            "data": {
                "message": "用户消息不能为空",
                "code": "CHAT_MESSAGE_REQUIRED",
                "status_code": 422,
                "detail": str(exc),
            },
        }
