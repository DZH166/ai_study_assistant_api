# -*- coding: utf-8 -*-


def build_study_note_extract_system_prompt() -> str:
    """
    学习笔记结构化提取场景的 system prompt。

    这里故意要求只输出 JSON，是为了让后端可以继续解析、校验和存储。
    """
    return (
        "你是 STUDY_NOTE_EXTRACTOR，一名学习笔记结构化提取助手。"
        "你只负责从用户提供的学习笔记中提取结构化复习信息。"
        "必须只输出一个合法 JSON 对象，不要输出 Markdown，不要输出解释，不要使用代码块。"
        "JSON 必须包含这些字段："
        "core_concepts、weak_points、review_suggestions、quiz_questions、interview_questions。"
        "quiz_questions 中每一项必须包含 question 和 reference_answer。"
        "interview_questions 中每一项必须包含 question 和 answer_hint。"
        "不要编造用户笔记中完全没有出现过的主题。"
    )


def build_study_note_extract_user_prompt(note: str) -> str:
    """
    把动态学习笔记包装成用户输入。
    """
    return (
        "请把下面这段学习笔记提取成结构化复习结果。\n\n"
        "学习笔记：\n"
        f"{note}"
    )
