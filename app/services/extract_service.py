# -*- coding: utf-8 -*-

from pydantic import ValidationError

from app.llm_client.client_factory import call_llm
from app.llm_client.llm_error_handler import LLMClientError
from app.prompts.extract_prompts import (
    build_study_note_extract_system_prompt,
    build_study_note_extract_user_prompt,
)
from app.prompts.repair_prompts import (
    build_study_note_repair_system_prompt,
    build_study_note_repair_user_prompt,
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


def parse_and_validate_extract(raw_answer: str) -> StudyNoteExtractData:
    """
    把模型原始字符串转换成经过校验的结构化对象。

    解析和校验必须分开理解：
    1. parse_json_object 负责确认它能不能变成 JSON/dict
    2. validate_extract_data 负责确认字段结构是不是我们要的
    """
    parsed_data = parse_json_object(raw_answer)
    return validate_extract_data(parsed_data)


def build_repair_messages(raw_answer: str, error_reason: str) -> list[ChatMessage]:
    """
    构造修复输出需要的 messages。

    修复任务只关心上一轮坏输出和错误原因，不让模型自由重做业务总结。
    """
    return [
        ChatMessage(role="system", content=build_study_note_repair_system_prompt()),
        ChatMessage(
            role="user",
            content=build_study_note_repair_user_prompt(
                broken_output=raw_answer,
                error_reason=error_reason,
            ),
        ),
    ]


def extract_study_note(request: StudyNoteExtractRequest) -> StudyNoteExtractResponse:
    """
    学习笔记结构化提取主流程。

    请求 -> Prompt -> 模型 -> JSON 解析 -> Pydantic 校验 -> 结构化响应
    """
    messages = build_extract_messages(request)
    llm_result = call_llm(messages=messages, temperature=request.temperature)
    raw_answer = llm_result["answer"]

    try:
        extraction = parse_and_validate_extract(raw_answer)
        repaired = False
        repair_reason = None
        final_raw_answer = raw_answer
    except (OutputParseError, ValidationError) as first_exc:
        repair_reason = str(first_exc)
        repair_messages = build_repair_messages(raw_answer, repair_reason)
        repair_result = call_llm(messages=repair_messages, temperature=0)
        repair_raw_answer = repair_result["answer"]

        try:
            extraction = parse_and_validate_extract(repair_raw_answer)
            repaired = True
            final_raw_answer = repair_raw_answer
            llm_result = repair_result
        except (OutputParseError, ValidationError) as second_exc:
            raise LLMClientError(
                message="模型输出结构不符合预期，自动修复后仍然失败",
                code="LLM_OUTPUT_REPAIR_FAILED",
                status_code=502,
                detail=f"first_error={first_exc}; repair_error={second_exc}",
            ) from second_exc

    return StudyNoteExtractResponse(
        extraction=extraction,
        model=llm_result["model"],
        usage=llm_result["usage"],
        repaired=repaired,
        repair_reason=repair_reason,
        raw_answer=final_raw_answer,
    )
