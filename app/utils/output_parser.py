# -*- coding: utf-8 -*-

import json
from json import JSONDecodeError


class OutputParseError(ValueError):
    """
    模型输出解析失败。

    模型输出本质上是不可信文本，不能默认它永远是合法 JSON。
    """


def parse_json_object(text: str) -> dict:
    """
    把模型输出的 JSON 字符串解析成 Python dict。

    真实模型有时会在 JSON 前后多输出解释文本，所以这里先尝试直接解析；
    如果失败，再尝试截取第一个 { 到最后一个 } 之间的内容。
    """
    cleaned_text = text.strip()

    try:
        result = json.loads(cleaned_text)
    except JSONDecodeError:
        start = cleaned_text.find("{")
        end = cleaned_text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise OutputParseError("模型输出不是合法 JSON 对象")

        try:
            result = json.loads(cleaned_text[start:end + 1])
        except JSONDecodeError as exc:
            raise OutputParseError("模型输出包含 JSON 片段，但格式不合法") from exc

    if not isinstance(result, dict):
        raise OutputParseError("模型输出必须是 JSON 对象")

    return result
