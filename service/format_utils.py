# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
import json
from typing import List, Dict, Any, Optional

from service.const import USER, SYSTEM, ASSISTANT
from service.model import Name, Message


def format_message(role: str, content: str, **kwargs):
    return {"role": role, "content": content}


def system_msg(content):
    return format_message(SYSTEM, content)


def user_msg(content):
    return format_message(USER, content)


def assistant_msg(content):
    return format_message(ASSISTANT, content)


def format_prompt_name(names: List[Name]):
    if not names:
        return "无"
    return "\n".join([f"- {str(n)}" for n in names])


def format_messages(messages: List[Message]) -> List[Dict]:
    if not messages:
        return []
    return [format_message(**m.model_dump()) for m in messages]


def extract_json(string: str) -> Optional[Any]:
    if string[:7].lower().startswith("```json"):
        string = string[7:]
    if string.startswith("```"):
        string = string[3:]
    if string.endswith("```"):
        string = string[:-3]
    try:
        return json.loads(string)
    except:
        return None
