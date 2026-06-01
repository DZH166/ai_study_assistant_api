# -*- coding: utf-8 -*-

from uuid import uuid4

from app.llm_client.client_factory import call_llm
from app.prompts.chat_prompts import build_system_prompt
from app.schemas.chat import ChatMessage, ChatRequest, ChatResponse


def create_conversation_id() -> str:
    """
    创建会话编号。

    工程意义：
    前端第一次聊天时可以不传 conversation_id，
    后端生成一个编号返回，下一轮对话继续带回来。
    """
    return f"conv_{uuid4().hex[:8]}"


def build_messages(request: ChatRequest) -> list[ChatMessage]:
    """
    把接口请求体转换成大模型需要的 messages。

    顺序非常重要：
    1. system：先给模型长期规则
    2. history：再给历史上下文
    3. user：最后放当前问题，让模型回答最新输入
    """
    system_prompt = build_system_prompt(request.prompt_scene)
    system_message = ChatMessage(role="system", content=system_prompt)
    user_message = ChatMessage(role="user", content=request.question)

    return [system_message] + request.history + [user_message]


def chat_with_ai(request: ChatRequest) -> ChatResponse:
    """
    聊天业务主流程。

    service 层像导演：它不接 HTTP，不直接关心前端；
    它负责组织 messages、调用模型客户端、整理最终业务结果。
    """
    messages = build_messages(request)
    llm_result = call_llm(messages=messages, temperature=request.temperature)

    conversation_id = request.conversation_id or create_conversation_id()

    return ChatResponse(
        answer=llm_result["answer"],
        conversation_id=conversation_id,
        model=llm_result["model"],
        usage=llm_result["usage"],
        messages_count=len(messages),
        fallback_used=llm_result.get("fallback_used", False),
        fallback_reason=llm_result.get("fallback_reason"),
    )
