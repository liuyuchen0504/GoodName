# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/9
# 
# ====================
from typing import List

from loguru import logger
from openai import OpenAI

from config.config import LLMSettings


llm_client = OpenAI(base_url=LLMSettings.BASE_URL, api_key=LLMSettings.API_KEY)


def ask_llm(
        messages: List,
        model: str,
        temperature: float = 1.0,
        stream: bool = False,
        **kwargs,
):
    logger.info(f"[LLMRequest] model={model}, messages={messages}")
    response = llm_client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=temperature,
        stream=stream,
        **kwargs,
    )
    logger.info(f"[LLMResponse] model={model}, response={response}")
    return response.choices[0].message.content
