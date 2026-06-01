# -*- coding: utf-8 -*-

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.llm_client.llm_error_handler import LLMClientError
from app.schemas.chat import ChatRequest
from app.services.chat_service import chat_with_ai
from app.utils.response import error_response, success_response


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
def chat(request: ChatRequest):
    """
    聊天接口入口。

    router 层只做三件事：
    1. 接收 HTTP 请求
    2. 把请求交给 service
    3. 把 service 的结果包装后返回
    """
    try:
        result = chat_with_ai(request)
    except LLMClientError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(
                message=exc.message,
                code=exc.code,
                detail=exc.detail,
            ),
        )

    # Pydantic v2 用 model_dump；如果遇到旧版本 Pydantic，则回退到 dict。
    data = result.model_dump() if hasattr(result, "model_dump") else result.dict()
    return success_response(message="聊天成功", data=data)
