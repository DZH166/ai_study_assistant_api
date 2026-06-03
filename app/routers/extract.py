# -*- coding: utf-8 -*-

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.llm_client.llm_error_handler import LLMClientError
from app.schemas.extract import StudyNoteExtractRequest
from app.services.extract_service import extract_study_note
from app.utils.response import error_response, success_response


router = APIRouter(prefix="/extract", tags=["extract"])


@router.post("/study-note")
def extract_study_note_api(request: StudyNoteExtractRequest):
    """
    学习笔记结构化提取接口。

    router 层只负责 HTTP 入口，不直接写 Prompt、不解析模型输出。
    """
    try:
        result = extract_study_note(request)
    except LLMClientError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(
                message=exc.message,
                code=exc.code,
                detail=exc.detail,
            ),
        )

    data = result.model_dump() if hasattr(result, "model_dump") else result.dict()
    return success_response(message="学习笔记提取成功", data=data)
