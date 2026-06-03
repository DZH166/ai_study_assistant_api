# -*- coding: utf-8 -*-

import json

from app.schemas.extract import StudyNoteExtractData


def build_study_note_repair_system_prompt() -> str:
    """
    结构化输出修复 Prompt。

    repair 不是重新做业务总结，而是把上一轮不合格输出修成合法 JSON。
    """
    return """
你是一名严格的 JSON 输出修复器。

你的任务：
把上一轮不合格的大模型输出修复成符合目标结构的合法 JSON。

规则：
1. 只返回合法 JSON 对象
2. 不要 Markdown
3. 不要代码块
4. 不要解释过程
5. 不要新增与原始内容无关的信息
6. 如果某些字段缺失，请根据原始输出和错误原因补齐合理内容
7. quiz_questions 每一项必须包含 question 和 reference_answer
8. interview_questions 每一项必须包含 question 和 answer_hint
"""


def build_study_note_repair_user_prompt(
    broken_output: str,
    error_reason: str,
) -> str:
    """
    把坏输出、错误原因和目标结构一起交给模型修复。
    """
    if hasattr(StudyNoteExtractData, "model_json_schema"):
        schema = StudyNoteExtractData.model_json_schema()
    else:
        schema = StudyNoteExtractData.schema()
    schema_json = json.dumps(schema, ensure_ascii=False)

    return f"""
上一轮模型输出不符合要求。

错误原因：
{error_reason}

上一轮原始输出：
{broken_output}

目标 JSON Schema：
{schema_json}

请只返回修复后的合法 JSON 对象。
"""
