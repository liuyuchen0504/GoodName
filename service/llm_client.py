# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/9
# 
# ====================
from typing import List

from openai import OpenAI

from config.config import LLMSettings


llm_client = OpenAI(base_url=LLMSettings.BASE_URL, api_key=LLMSettings.API_KEY)


def ask_llm(
        messages: List,
        model: str,
        stream: bool = False,
):
    response = llm_client.chat.completions.create(
        messages=messages,
        model=model,
        stream=stream,
    )
    return response.choices[0].message.content
