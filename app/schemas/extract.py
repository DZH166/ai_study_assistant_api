# -*- coding: utf-8 -*-

from pydantic import BaseModel, Field


class StudyNoteExtractRequest(BaseModel):
    """
    /extract/study-note 请求体。

    note 是用户输入的一段学习笔记，后端会让模型把它提取成固定结构。
    """
    note: str = Field(..., min_length=1, description="需要结构化提取的学习笔记内容")
    temperature: float = Field(default=0.2, ge=0, le=2, description="模型发散程度，提取任务建议偏低")


class QuizQuestion(BaseModel):
    """
    用于当天知识点抽问。
    """
    question: str = Field(..., min_length=1, description="抽问问题")
    reference_answer: str = Field(..., min_length=1, description="参考答案")


class InterviewQuestion(BaseModel):
    """
    用于累计面试训练。
    """
    question: str = Field(..., min_length=1, description="面试题")
    answer_hint: str = Field(..., min_length=1, description="回答提示")


class StudyNoteExtractData(BaseModel):
    """
    AI 输出经过解析和校验后的结构化结果。

    这层模型的意义：
    AI 生成的是文本，后端必须把它校验成稳定字段，才能继续被前端、数据库或复习系统使用。
    """
    core_concepts: list[str] = Field(..., description="核心知识点")
    weak_points: list[str] = Field(..., description="薄弱点")
    review_suggestions: list[str] = Field(..., description="复习建议")
    quiz_questions: list[QuizQuestion] = Field(..., description="知识点抽问题")
    interview_questions: list[InterviewQuestion] = Field(..., description="面试题")


class StudyNoteExtractResponse(BaseModel):
    """
    /extract/study-note 响应体里的 data。
    """
    extraction: StudyNoteExtractData
    model: str
    usage: dict
    raw_answer: str | None = Field(default=None, description="调试用原始模型输出，正式生产可关闭")
