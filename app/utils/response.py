# -*- coding: utf-8 -*-


def success_response(message: str, data=None):
    """
    统一成功响应。

    工程重点：
    1. 前端不用猜接口成功时返回什么字段。
    2. 后端以后想加日志、trace_id、分页信息，也有统一位置。
    3. 每个 router 不需要重复手写同一套响应结构。
    """
    return {
        "success": True,
        "message": message,
        "data": data,
        "error": None,
    }


def error_response(message: str, code: str, detail: str | None = None):
    """
    统一错误响应。

    message 给调用方看，code 给程序判断，detail 给开发排查。
    """
    return {
        "success": False,
        "message": message,
        "data": None,
        "error": {
            "code": code,
            "detail": detail,
        },
    }

