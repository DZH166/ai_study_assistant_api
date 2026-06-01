# -*- coding: utf-8 -*-

from app.schemas.chat import ChatMessage


def call_mock_llm(
    messages: list[ChatMessage],
    temperature: float,
    model_name: str,
) -> dict:
    """
    模拟大模型调用。

    现在先不用真实 API，是为了专注理解 /chat 的工程链路：
    router -> schema -> service -> llm_client -> response。
    等链路稳定后，只需要替换这个 client，就可以接入真实模型。

    model_name 来自 .env 配置，而不是写死在函数里。
    这就是 Module16 的重点：会变的东西交给配置，不要散落在业务代码里。
    """
    latest_user_message = messages[-1].content

    answer = (
        "这是 mock 模型回答：我已经收到你的问题："
        f"{latest_user_message}。当前 temperature={temperature}。"
    )

    return {
        "answer": answer,
        "model": model_name,
        "usage": {
            "prompt_tokens": len(str(messages)),
            "completion_tokens": len(answer),
            "total_tokens": len(str(messages)) + len(answer),
        },
    }
