# -*- coding: utf-8 -*-

from fastapi import FastAPI

from app.core.config import get_settings
from app.routers import chat, extract
from app.utils.response import success_response


app = FastAPI(
    title="AI Study Assistant API",
    description="AI 学习陪跑助手后端，支持聊天、Prompt 场景和学习笔记结构化提取。",
    version="1.2.0",
)


# 把 chat.py 里的接口统一挂到主应用上。
# main.py 是主应用入口，不应该堆业务细节。
app.include_router(chat.router)
app.include_router(extract.router)


@app.get("/")
def read_root():
    settings = get_settings()
    return success_response(
        message="欢迎进入 Module16 Configurable Chat API",
        data={
            "docs": "访问 /docs 查看接口文档",
            "chat_api": "POST /chat",
            "extract_api": "POST /extract/study-note",
            "config": settings.safe_dict(),
        },
    )


@app.get("/health")
def check_health():
    settings = get_settings()
    return success_response(
        message="服务运行正常",
        data={
            "status": "ok",
            "config": settings.safe_dict(),
        },
    )
