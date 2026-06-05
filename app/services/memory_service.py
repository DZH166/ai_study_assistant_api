# -*- coding: utf-8 -*-

from dataclasses import dataclass

from app.data.conversation_store import (
    MAX_HISTORY_ROUNDS,
    get_conversation,
    get_messages_ready_for_summary,
    update_summary_memory,
)
from app.llm_client.client_factory import call_llm
from app.llm_client.llm_error_handler import LLMClientError
from app.schemas.chat import ChatMessage, MessageItem


SUMMARY_MEMORY_ROLE = "system"


@dataclass
class MemorySummaryResult:
    """
    摘要记忆更新结果。

    service 层用它决定响应里如何展示 memory_summary 状态。
    """
    summary_memory: str | None
    updated: bool = False
    failed: bool = False
    error: str | None = None

    @property
    def used(self) -> bool:
        return bool(self.summary_memory)


def format_history_for_summary(messages: list[MessageItem]) -> str:
    """
    把历史消息转换成适合摘要模型阅读的文本。
    """
    return "\n".join(
        f"{message.role}: {message.content}"
        for message in messages
    )


def build_summary_messages(
    previous_summary: str | None,
    messages_to_summarize: list[MessageItem],
) -> list[ChatMessage]:
    """
    构造摘要压缩专用 messages。

    这里不是让模型继续聊天，而是让模型把旧上下文压缩成可复用记忆。
    """
    system_prompt = """
你是 MEMORY_SUMMARIZER，会把较早的学习对话压缩成后端可复用的 summary memory。

只保留对后续学习有价值的信息：
1. 用户长期学习目标
2. 已讨论的关键知识点
3. 用户暴露的薄弱点
4. 当前任务状态
5. 后续回答需要延续的上下文

不要保存寒暄、重复确认、无意义情绪表达。
用简洁中文输出一段摘要，不要输出 JSON。
""".strip()

    previous_summary_text = previous_summary or "暂无"
    history_text = format_history_for_summary(messages_to_summarize)
    user_content = f"""
已有摘要记忆：
{previous_summary_text}

本次需要压缩进摘要的新旧消息：
{history_text}

请生成更新后的 summary memory。
""".strip()

    return [
        ChatMessage(role="system", content=system_prompt),
        ChatMessage(role="user", content=user_content),
    ]


def build_summary_memory_message(summary_memory: str) -> ChatMessage:
    """
    把摘要记忆包装成发给大模型的 system 消息。
    """
    content = f"""
以下是此前较早对话的压缩记忆。它不是用户当前问题，而是帮助你理解上下文的背景信息：

{summary_memory}
""".strip()
    return ChatMessage(role=SUMMARY_MEMORY_ROLE, content=content)


def refresh_summary_memory(conversation_id: str) -> MemorySummaryResult:
    """
    如果存在需要压缩的旧消息，就更新 summary_memory。

    摘要失败不阻断聊天主流程；调用方会在响应中记录失败状态。
    """
    conversation = get_conversation(conversation_id)
    messages_to_summarize = get_messages_ready_for_summary(
        conversation_id=conversation_id,
        max_rounds=MAX_HISTORY_ROUNDS,
    )

    if not messages_to_summarize:
        return MemorySummaryResult(summary_memory=conversation.summary_memory)

    try:
        llm_result = call_llm(
            messages=build_summary_messages(
                previous_summary=conversation.summary_memory,
                messages_to_summarize=messages_to_summarize,
            ),
            temperature=0.1,
        )
    except LLMClientError as exc:
        return MemorySummaryResult(
            summary_memory=conversation.summary_memory,
            failed=True,
            error=exc.code,
        )

    summary_memory = llm_result["answer"]
    summarized_messages_count = conversation.summarized_messages_count + len(messages_to_summarize)
    update_summary_memory(
        conversation_id=conversation_id,
        summary_memory=summary_memory,
        summarized_messages_count=summarized_messages_count,
    )

    return MemorySummaryResult(summary_memory=summary_memory, updated=True)

