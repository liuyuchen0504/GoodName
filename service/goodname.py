# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
from typing import List, Optional, Dict

from sqlmodel.ext.asyncio.session import AsyncSession

from config.config import LLMSettings, StyleSettings
from service.const import LIKE, UNKNOWN
from service.db.message_op import MessageOp
from service.db.name_op import NameOp
from service.format_utils import system_msg, user_msg, format_prompt_name, \
    format_messages, extract_json, assistant_msg
from service.llm_client import ask_llm
from service.model import Name, Message
from service.model.name import NameCreate
from service.prompt import SYSTEM_PROMPT, OUTPUT_FORMAT


class GoodNameService:

    @classmethod
    async def generate_names(
            cls,
            session: AsyncSession,
            query: str,
            session_id: str,
            user_id: str,       # 没啥用，只是 name 中需要
            system_prompt: Optional[str] = None,
            style_prompt: Optional[Dict[str, str]] = None,
            style: List[str] = [],
            current_like_name: List[Name] = [],
            model: str = "deepseek-v3",
            temperature: float = 1.0,
    ):
        # 0. 保存用户信息
        await MessageOp.insert_message(session, Message(**user_msg(query), session_id=session_id))
        # 1. 获取所有已经生成的名字
        names = await NameOp.query_name_by_session_id(session=session, session_id=session_id)
        like_names = [n for n in names if n.prefer == LIKE]
        unknown_names = [n for n in names if n.prefer == UNKNOWN]
        not_like_names = list(await NameOp.query_name_by_session_id(session=session, session_id=session_id, is_valid=False))

        # 2. 获取所有历史对话信息
        history = await MessageOp.query_message_by_session_id(session=session, session_id=session_id)

        # 3. 拼接生成 Prompt
        system_prompt = (system_prompt or SYSTEM_PROMPT).format(
            style=StyleSettings.format_styles_prompt(style, style_prompt),
            name=format_prompt_name(unknown_names),
            like_name=format_prompt_name(like_names),
            not_like_name=format_prompt_name(not_like_names),
            current_like_name=format_prompt_name(current_like_name),
        )
        ## 输出格式要求
        system_prompt += OUTPUT_FORMAT

        messages = [system_msg(system_prompt)] + format_messages(history) + [user_msg(query)]

        print(messages)
        # 4. 调用大模型
        response = ask_llm(
            model=LLMSettings.get_model(model),
            messages=messages,
            temperature=temperature,
        )

        # 5. 解析结果
        result = extract_json(response)

        llm_names = []
        if result:
            had_names = []
            for r in result:
                try:
                    if r.get("name") in had_names:
                        continue
                    llm_names.append(NameCreate(**r, session_id=session_id, user_id=user_id))
                    had_names.append(r.name)
                except:
                    pass

        print(llm_names)
        # 6. 保存 name
        new_names = await NameOp.insert_names(session, llm_names)
        print(new_names)

        # 7 保存生成会话
        content = f"给您取了如下名字：{'，'.join([n.name for n in new_names])}" if new_names else "没有新的姓名"
        await MessageOp.insert_message(session, Message(**assistant_msg(content), session_id=session_id))

        for n in new_names:
            await session.refresh(n)

        return new_names

