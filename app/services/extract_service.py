# -*- coding: utf-8 -*-

from pydantic import ValidationError

from app.llm_client.client_factory import call_llm
from app.llm_client.llm_error_handler import LLMClientError
from app.prompts.extract_prompts import (
    build_study_note_extract_system_prompt,
    build_study_note_extract_user_prompt,
)
from app.schemas.chat import ChatMessage
from app.schemas.extract import (
    StudyNoteExtractData,
    StudyNoteExtractRequest,
    StudyNoteExtractResponse,
)
from app.utils.output_parser import OutputParseError, parse_json_object


def build_extract_messages(request: StudyNoteExtractRequest) -> list[ChatMessage]:
    """
    构造学习笔记提取任务需要的 messages。

    system 负责约束输出格式，user 放真正要处理的学习笔记。
    """
    return [
        ChatMessage(role="system", content=build_study_note_extract_system_prompt()),
        ChatMessage(role="user", content=build_study_note_extract_user_prompt(request.note)),
    ]


def validate_extract_data(data: dict) -> StudyNoteExtractData:
    """
    用 Pydantic 校验模型输出结构。

    这一步是 Module21 的关键：
    Prompt 只能要求模型输出 JSON，但后端必须用代码确认字段真的符合预期。
    """
    if hasattr(StudyNoteExtractData, "model_validate"):
        return StudyNoteExtractData.model_validate(data)
    return StudyNoteExtractData.parse_obj(data)


def extract_study_note(request: StudyNoteExtractRequest) -> StudyNoteExtractResponse:
    """
    学习笔记结构化提取主流程。

    请求 -> Prompt -> 模型 -> JSON 解析 -> Pydantic 校验 -> 结构化响应
    """
    messages = build_extract_messages(request)
    llm_result = call_llm(messages=messages, temperature=request.temperature)
    raw_answer = llm_result["answer"]

    try:
        parsed_data = parse_json_object(raw_answer)
        extraction = validate_extract_data(parsed_data)
    except (OutputParseError, ValidationError) as exc:
        raise LLMClientError(
            message="模型输出结构不符合预期",
            code="LLM_OUTPUT_PARSE_ERROR",
            status_code=502,
            detail=str(exc),
        ) from exc

    return StudyNoteExtractResponse(
        extraction=extraction,
        model=llm_result["model"],
        usage=llm_result["usage"],
        raw_answer=raw_answer,
    )
