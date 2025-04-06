# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/9
# 
# ====================
import json
import re
from typing import List, Optional, Literal

from loguru import logger
from openai import OpenAI
from fastapi import WebSocket
from openai.types.chat import ChatCompletionMessage
from pydantic import BaseModel
from pypinyin import pinyin

from config.config import LLMSettings
from service.model.card import Card, NameCard
from service.model.params import BasicInfo

llm_client = OpenAI(base_url=LLMSettings.BASE_URL, api_key=LLMSettings.API_KEY)


class ReasoningChatCompletionMessage(ChatCompletionMessage):
    reasoning_content: Optional[str] = None
    """The reasoning contents of the message."""

    role: Literal["assistant"] = "assistant"
    """The role of the author of this message."""


class DeltaMessage(BaseModel):
    type: Literal["message.delta", "action", "completion", "ping"]
    content: Optional[str] = None
    card: Optional[Card] = None


async def ask_llm(
        messages: List,
        model: str,
        temperature: float = 1.0,
        stream: bool = True,
        websocket: WebSocket = None,
        context: BasicInfo = None,
        **kwargs,
):
    logger.info(f"[LLMRequest] model={model}, messages={messages}")
    stream = llm_client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=temperature,
        stream=stream,
    )
    response = ReasoningChatCompletionMessage(content="")
    current_card = ""
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            response.content += delta.content
            # 卡片检测
            current_card += delta.content
            if matcher := re.search(r"\{.*\}", current_card, re.S):
                if websocket:
                    name = json.loads(matcher.group(0))
                    if not name["name"].startswith(context.last_name):
                        name["name"] = f"{context.last_name}{name['name']}"
                    name["pinyin"] = " ".join([p[0] for p in pinyin(name["name"])])
                    name["gender"] = context.gender
                    if shengchenbazi := kwargs.get("shengchenbazi"):
                        name["shengchenbazi"] = shengchenbazi
                    card = NameCard(data=name)
                    await websocket.send_json(DeltaMessage(type="message.delta", card=card).model_dump())
                    current_card = current_card.split("}")[-1]
        # openai client 暂时不支持
        # elif delta.reasoning_content:
        #     response.reasoning_content += delta.reasoning_content
    logger.info(f"[LLMResponse] model={model}, response={response.model_dump()}")
    return response
