# -*- coding: utf-8 -*-

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
    role: str
    content: str


class ChatRequest(BaseModel):
    """
    /chat 接口请求体。

    这不是模型最终需要的格式，而是前端调用后端时提交的业务数据。
    后端会在 service 层把它转换成大模型需要的 messages。
    """
    question: str = Field(..., min_length=1, description="用户当前问题")
    conversation_id: str | None = Field(default=None, description="会话编号，首次对话可以为空")
    history: list[ChatMessage] = Field(default_factory=list, description="历史消息，用于多轮对话")
    temperature: float = Field(default=0.3, ge=0, le=2, description="模型发散程度")
    prompt_scene: Literal["learning_assistant", "interview_assistant", "summary_assistant"] = Field(
        default="learning_assistant",
        description="Prompt 场景，决定当前 /chat 使用哪种 system prompt",
    )


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
    fallback_used: bool = False
    fallback_reason: str | None = None
