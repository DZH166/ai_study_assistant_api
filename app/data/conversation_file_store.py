# -*- coding: utf-8 -*-

import json
import re
from pathlib import Path

from app.schemas.chat import Conversation


STORAGE_DIR = Path(__file__).resolve().parents[1] / "storage" / "conversations"
CONVERSATION_ID_PATTERN = re.compile(r"^conv_[a-f0-9]{8}$")


def get_conversation_file_path(conversation_id: str) -> Path:
    """
    Return the JSON file path for one conversation.

    The id check prevents a user-provided conversation_id from becoming a
    filesystem path such as ../../secret.txt.
    """
    if not CONVERSATION_ID_PATTERN.fullmatch(conversation_id):
        raise FileNotFoundError(f"Invalid conversation_id: {conversation_id}")

    return STORAGE_DIR / f"{conversation_id}.json"


def conversation_to_dict(conversation: Conversation) -> dict:
    """
    Serialize a Conversation object into plain Python data.

    JSON can store dict/list/str/int/bool/None, but it does not know how to
    store a Pydantic Conversation object directly.
    """
    if hasattr(conversation, "model_dump"):
        return conversation.model_dump()

    return conversation.dict()


def conversation_from_dict(data: dict) -> Conversation:
    """
    Deserialize plain Python data back into a Conversation object.
    """
    if hasattr(Conversation, "model_validate"):
        return Conversation.model_validate(data)

    return Conversation(**data)


def save_conversation(conversation: Conversation) -> None:
    """
    Persist one conversation to a JSON file.
    """
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    path = get_conversation_file_path(conversation.conversation_id)
    data = conversation_to_dict(conversation)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_conversation(conversation_id: str) -> Conversation:
    """
    Load one conversation from disk.
    """
    path = get_conversation_file_path(conversation_id)
    if not path.exists():
        raise FileNotFoundError(f"Conversation file not found: {conversation_id}")

    data = json.loads(path.read_text(encoding="utf-8"))
    return conversation_from_dict(data)


def conversation_file_exists(conversation_id: str) -> bool:
    """
    Check whether a persisted conversation exists.
    """
    return get_conversation_file_path(conversation_id).exists()
