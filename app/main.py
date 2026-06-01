# -*- coding: utf-8 -*-

from fastapi import FastAPI

from app.core.config import get_settings
from app.routers import chat
from app.utils.response import success_response


app = FastAPI(
    title="Module16 Configurable Chat API",
    description="在 /chat 项目中加入 .env、环境变量和模型配置管理。",
    version="1.1.0",
)


# 把 chat.py 里的接口统一挂到主应用上。
# main.py 是主应用入口，不应该堆业务细节。
app.include_router(chat.router)


@app.get("/")
def read_root():
    settings = get_settings()
    return success_response(
        message="欢迎进入 Module16 Configurable Chat API",
        data={
            "docs": "访问 /docs 查看接口文档",
            "chat_api": "POST /chat",
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
