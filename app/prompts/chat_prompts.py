# -*- coding: utf-8 -*-

from typing import Literal


PromptScene = Literal[
    "learning_assistant",
    "interview_assistant",
    "summary_assistant",
]


def build_learning_assistant_prompt() -> str:
    """
    学习助手场景：
    更适合解释概念、拆解知识点、辅助理解代码。
    """
    return (
        "你是一名严谨、清晰、耐心的 AI 应用开发学习助手。"
        "你要优先帮助用户理解概念、工程意义、代码结构和易错点。"
        "如果用户问的是技术问题，回答要尽量结构化、准确、便于复习。"
    )


def build_interview_assistant_prompt() -> str:
    """
    面试助手场景：
    更适合把同一个知识点压缩成更像面试回答的表达。
    """
    return (
        "你是一名 AI 应用开发面试辅导助手。"
        "请优先把回答整理成更接近面试表达的版本，"
        "强调结论、原理、工程取舍和常见追问。"
    )


def build_summary_assistant_prompt() -> str:
    """
    总结助手场景：
    更适合把当天学习内容整理成复习提纲。
    """
    return (
        "你是一名学习总结助手。"
        "请基于用户提供的学习内容，提炼重点、难点、易错点和面试点。"
        "不要编造用户没有学过的内容。"
    )


def build_system_prompt(scene: PromptScene) -> str:
    """
    根据场景构建 system prompt。

    工程意义：
    1. service 层不再直接维护大段 Prompt 文本
    2. 不同业务场景可以复用同一个 /chat 接口
    3. 后续新增 Prompt 场景时，主要改 prompts 层
    """
    prompt_builders = {
        "learning_assistant": build_learning_assistant_prompt,
        "interview_assistant": build_interview_assistant_prompt,
        "summary_assistant": build_summary_assistant_prompt,
    }
    return prompt_builders[scene]()

