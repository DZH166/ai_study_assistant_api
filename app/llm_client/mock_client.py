# -*- coding: utf-8 -*-

import json

from app.schemas.chat import ChatMessage


def build_mock_study_note_extract_answer(latest_user_message: str) -> str:
    """
    为学习笔记提取场景返回稳定 JSON。

    mock 的目标不是假装模型很聪明，而是让后端链路可以在没有真实 API Key 时跑通：
    Prompt -> LLM -> JSON 解析 -> Pydantic 校验 -> 统一响应。
    """
    result = {
        "core_concepts": [
            "结构化输出可以把模型生成的文本转换成后端可处理的数据",
            "Prompt 负责约束模型输出格式，Pydantic 负责校验输出结构",
            "学习笔记提取接口需要经过请求、模型、解析、校验和响应几个步骤",
        ],
        "weak_points": [
            "容易把普通文本回答和结构化 JSON 输出混在一起",
            "容易默认相信模型一定会输出合法 JSON",
        ],
        "review_suggestions": [
            "复习 JSON 字符串、Python dict 和 Pydantic 模型之间的关系",
            "画出 /extract/study-note 的完整调用链路",
        ],
        "quiz_questions": [
            {
                "question": "为什么 AI 应用不能只返回普通文本？",
                "reference_answer": "普通文本适合人看，但不稳定，后端难以继续解析、存储和统计。",
            },
            {
                "question": "Pydantic 在结构化输出里负责什么？",
                "reference_answer": "负责校验模型输出字段是否存在、类型是否符合预期。",
            },
        ],
        "interview_questions": [
            {
                "question": "你如何保证大模型输出能被后端稳定处理？",
                "answer_hint": "通过 Prompt 约束输出格式，再用 JSON 解析和 Pydantic 校验做兜底。",
            }
        ],
    }
    return json.dumps(result, ensure_ascii=False)


def build_mock_repair_answer(latest_user_message: str) -> str:
    """
    为 repair 场景返回合法 JSON。

    真实模型会根据坏输出和错误原因修复；mock 只需要模拟“修复后可通过校验”的结果。
    """
    result = {
        "core_concepts": [
            "模型输出修复用于处理结构化输出不稳定问题",
            "解析失败和校验失败需要被后端区分和兜底",
        ],
        "weak_points": [
            "容易把 repair 理解成重新生成业务答案",
        ],
        "review_suggestions": [
            "记住 repair 的目标是修格式，不是重新自由总结",
        ],
        "quiz_questions": [
            {
                "question": "为什么结构化输出失败后不能直接返回原始结果？",
                "reference_answer": "因为原始结果不稳定，前端和后端都难以继续处理。",
            }
        ],
        "interview_questions": [
            {
                "question": "你如何处理大模型没有按 JSON 格式返回的情况？",
                "answer_hint": "先解析和校验，失败后用 repair prompt 有限重试，仍失败则返回统一错误。",
            }
        ],
    }
    return json.dumps(result, ensure_ascii=False)


def build_mock_memory_summary_answer(latest_user_message: str) -> str:
    """
    为会话记忆压缩场景返回稳定摘要。

    mock 不负责真正理解全部历史，只负责让 Module24 的压缩链路可测试。
    """
    return (
        "用户正在学习 AI 应用开发，当前主线是把聊天接口升级成具备上下文能力的学习助手。"
        "此前已讨论过 router/schema/service/llm_client 分层、messages 组装、多轮对话和 conversation_id。"
        "用户容易在代码阅读时把数据结构、业务流程和模型适配层联系不起来，后续回答应继续强调执行链路、职责边界和工程化原因。"
        f"本次压缩依据：{latest_user_message[:120]}"
    )


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
    system_prompt = messages[0].content if messages else ""

    if "JSON 输出修复器" in system_prompt:
        answer = build_mock_repair_answer(latest_user_message)
    elif "MEMORY_SUMMARIZER" in system_prompt:
        answer = build_mock_memory_summary_answer(latest_user_message)
    elif "STUDY_NOTE_EXTRACTOR" in system_prompt:
        answer = build_mock_study_note_extract_answer(latest_user_message)
    else:
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
