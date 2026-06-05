# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """
    单条聊天消息。

    role 表示这句话是谁说的：
    - system：长期规则和边界
    - user：用户输入
    - assistant：模型历史回答
    """
    role: Literal["system", "user", "assistant"]
    content: str


class MessageItem(BaseModel):
    """
    后端保存的一条历史消息。

    和 ChatMessage 的区别：
    - ChatMessage 是发给大模型的消息格式
    - MessageItem 是后端会话存储里的消息记录
    """
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


class Conversation(BaseModel):
    """
    一场完整对话。

    Module23 先用内存保存它，Module25 再升级成文件或数据库持久化。
    """
    conversation_id: str
    mode: Literal["study", "interview", "summary"] = "study"
    messages: list[MessageItem] = Field(default_factory=list)
    summary_memory: str | None = Field(default=None, description="较早对话压缩后的摘要记忆")
    summarized_messages_count: int = Field(default=0, description="已经被压缩进摘要记忆的消息数量")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


class ChatRequest(BaseModel):
    """
    /chat 接口请求体。

    这不是模型最终需要的格式，而是前端调用后端时提交的业务数据。
    后端会在 service 层把它转换成大模型需要的 messages。
    """
    message: str | None = Field(default=None, min_length=1, description="用户当前消息，Module23 新字段")
    question: str | None = Field(default=None, min_length=1, description="用户当前问题，兼容旧字段")
    conversation_id: str | None = Field(default=None, description="会话编号，首次对话可以为空")
    history: list[ChatMessage] = Field(default_factory=list, description="历史消息，用于多轮对话")
    temperature: float = Field(default=0.3, ge=0, le=2, description="模型发散程度")
    mode: Literal["study", "interview", "summary"] = Field(
        default="study",
        description="聊天模式，Module23 新字段",
    )
    prompt_scene: Literal["learning_assistant", "interview_assistant", "summary_assistant"] | None = Field(
        default=None,
        description="Prompt 场景，决定当前 /chat 使用哪种 system prompt",
    )

    def current_message(self) -> str:
        """
        返回当前用户输入。

        新接口优先用 message，旧接口兼容 question。
        """
        if self.message:
            return self.message
        if self.question:
            return self.question
        raise ValueError("message 不能为空")

    def current_prompt_scene(self) -> Literal["learning_assistant", "interview_assistant", "summary_assistant"]:
        """
        把业务 mode 转换成已有的 prompt_scene。
        """
        if self.prompt_scene:
            return self.prompt_scene
        mode_to_scene = {
            "study": "learning_assistant",
            "interview": "interview_assistant",
            "summary": "summary_assistant",
        }
        return mode_to_scene[self.mode]  # type: ignore[return-value]


class ChatResponse(BaseModel):
    """
    /chat 接口响应体里的核心 data。

    answer 用于展示，conversation_id/model/usage 用于后续多轮、排查和成本统计。
    """
    answer: str
    conversation_id: str
    model: str
    usage: dict
    messages_count: int
    history_rounds: int = Field(default=0, description="当前会话已保存的轮数")
    stored_messages_count: int = Field(default=0, description="当前会话已保存的消息条数")
    memory_summary: str | None = Field(default=None, description="当前会话的摘要记忆")
    memory_summary_used: bool = Field(default=False, description="本次调用是否把摘要记忆放入 messages")
    memory_summary_updated: bool = Field(default=False, description="本次调用是否更新了摘要记忆")
    memory_summary_failed: bool = Field(default=False, description="本次调用是否尝试更新摘要但失败")
    memory_summary_error: str | None = Field(default=None, description="摘要记忆更新失败原因")
    fallback_used: bool = False
    fallback_reason: str | None = None
