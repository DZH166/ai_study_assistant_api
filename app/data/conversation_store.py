# -*- coding: utf-8 -*-

from uuid import uuid4

from app.schemas.chat import Conversation, MessageItem


MAX_HISTORY_ROUNDS = 3

_CONVERSATIONS: dict[str, Conversation] = {}


class ConversationNotFoundError(ValueError):
    """
    会话不存在。

    service 层会把它转换成对前端友好的 404 错误。
    """


def create_conversation(mode: str) -> Conversation:
    """
    创建新会话并保存到内存。
    """
    conversation_id = f"conv_{uuid4().hex[:8]}"
    conversation = Conversation(conversation_id=conversation_id, mode=mode)
    _CONVERSATIONS[conversation_id] = conversation
    return conversation


def get_conversation(conversation_id: str) -> Conversation:
    """
    根据 conversation_id 读取会话。
    """
    conversation = _CONVERSATIONS.get(conversation_id)
    if conversation is None:
        raise ConversationNotFoundError(f"会话不存在：{conversation_id}")
    return conversation


def append_message(conversation_id: str, role: str, content: str) -> None:
    """
    保存一条 user 或 assistant 消息。
    """
    conversation = get_conversation(conversation_id)
    conversation.messages.append(MessageItem(role=role, content=content))  # type: ignore[arg-type]
    conversation.updated_at = conversation.messages[-1].created_at


def get_recent_history(conversation_id: str, max_rounds: int = MAX_HISTORY_ROUNDS) -> list[MessageItem]:
    """
    读取最近 N 轮历史。

    一轮通常包含 1 条 user + 1 条 assistant，所以 N 轮大约是 2N 条消息。
    """
    conversation = get_conversation(conversation_id)
    max_messages = max_rounds * 2
    return conversation.messages[-max_messages:]


def count_rounds(conversation_id: str) -> int:
    """
    统计当前会话已保存多少轮。
    """
    conversation = get_conversation(conversation_id)
    user_messages = sum(1 for message in conversation.messages if message.role == "user")
    assistant_messages = sum(1 for message in conversation.messages if message.role == "assistant")
    return min(user_messages, assistant_messages)


def count_messages(conversation_id: str) -> int:
    """
    统计当前会话已保存多少条消息。
    """
    return len(get_conversation(conversation_id).messages)


def clear_conversations() -> None:
    """
    测试辅助函数：清空内存会话。
    """
    _CONVERSATIONS.clear()
