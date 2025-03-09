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

from config.config import LLMSettings
from service.model.card import Card, NameCard

llm_client = OpenAI(base_url=LLMSettings.BASE_URL, api_key=LLMSettings.API_KEY)


class ReasoningChatCompletionMessage(ChatCompletionMessage):
    reasoning_content: Optional[str] = None
    """The reasoning contents of the message."""

    role: Literal["assistant"] = "assistant"
    """The role of the author of this message."""


class DeltaMessage(BaseModel):
    type: Literal["message.delta", "action", "completion"]
    content: Optional[str] = None
    card: Optional[Card] = None


async def ask_llm(
        messages: List,
        model: str,
        temperature: float = 1.0,
        stream: bool = True,
        websocket: WebSocket = None,
        **kwargs,
):
    logger.info(f"[LLMRequest] model={model}, messages={messages}")
    stream = llm_client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=temperature,
        stream=stream,
        **kwargs,
    )
    response = ReasoningChatCompletionMessage(content="")
    current_card = ""
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            response.content += delta.content
            # 卡片检测
            if "{" in delta.content:
                current_card = delta.content
            elif current_card:
                current_card += delta.content
            if matcher := re.search(r"\{.*\}", current_card, re.S):
                if websocket:
                    card = NameCard(data=json.loads(matcher.group(0)))
                    await websocket.send_json(DeltaMessage(content=delta.content, type="message.delta", card=card).model_dump())
                    current_card = current_card.replace(matcher.group(0), "")
        # openai client 暂时不支持
        # elif delta.reasoning_content:
        #     response.reasoning_content += delta.reasoning_content
    logger.info(f"[LLMResponse] model={model}, response={response.model_dump()}")
    return response
