# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
import random
from typing import List, Optional, Dict, Any

from loguru import logger
from sqlmodel.ext.asyncio.session import AsyncSession

from config.config import LLMSettings, StyleSettings
from service.const import LIKE
from service.db.message_op import MessageOp
from service.db.name_op import NameOp
from service.format_utils import user_msg, extract_json, assistant_msg, \
    system_msg, format_messages
from service.llm_client import ask_llm
from service.model import Name, Message
from service.model.name import NameCreate
from service.prompts import PromptFactory


class GoodNameService:

    @staticmethod
    async def check_and_intention(
            session: AsyncSession,
            session_id: str,
            model: str = "deepseek-v3"
    ) -> Dict[str, str]:
        history = await MessageOp.query_message_by_session_id(session=session, session_id=session_id)
        prompt = PromptFactory.format_template(prompt_name="intention_prompt")
        response = ask_llm(
            model=LLMSettings.get_model(model),
            messages=[system_msg(prompt)] + format_messages(history),
        )
        return extract_json(response)


    @classmethod
    async def generate_names(
            cls,
            session: AsyncSession,
            query: str,
            session_id: str,
            user_id: str,       # 没啥用，只是 name 中需要
            last_name: str = None,
            sex: str = None,
            system_prompt: Optional[str] = None,
            style_prompt: Optional[Dict[str, str]] = None,
            style: List[str] = [],
            current_like_name: List[Name] = [],
            model: str = "deepseek-v3",
            temperature: float = 1.0,
            debug: bool = False,
    ) -> Dict[str, Any]:
        await MessageOp.insert_message(session, Message(**user_msg(query), session_id=session_id))
        # 1. 获取所有已经生成的名字
        names = await NameOp.query_name_by_session_id(session=session, session_id=session_id)
        like_names = [n for n in names if n.prefer == LIKE]
        unlike_names = list(await NameOp.query_name_by_session_id(session=session, session_id=session_id, is_valid=False))

        # 2. 获取所有历史对话信息
        history = await MessageOp.query_message_by_session_id(session=session, session_id=session_id)

        # 3. 获取选择的风格
        styles = StyleSettings.get_selected_styles(style, style_prompt)

        # 4. Prompt
        if styles:
            prompt_type = "good_name_default_prompt"
        else:
            prompt_type = random.choice(["good_name_combine_prompt", "good_name_default_prompt"])
        prompt = PromptFactory.format_template(
            prompt_name=prompt_type,
            user_prompt=system_prompt,
            styles=styles,
            messages=history,
            like_names=like_names,
            unlike_names=unlike_names,
            current_like_name=current_like_name,
            last_name=last_name,
            sex=sex,
        )

        messages = [system_msg(prompt)] + format_messages(history)

        # 4. 调用大模型
        response = ask_llm(
            model=LLMSettings.get_model(model),
            messages=messages,
            temperature=temperature,
        )

        # 5. 解析结果
        result = extract_json(response, r"\[.*\]")
        new_names = None
        if isinstance(result, str):
            pass
        else:
            llm_names = []
            if result:
                had_names = []
                for r in result:
                    try:
                        if r.get("name") in had_names:
                            continue
                        llm_names.append(NameCreate(**r, session_id=session_id, user_id=user_id))
                        had_names.append(r["name"])
                    except Exception as e:
                        logger.warning(f"[SAVE_NAME] name={r} error={e}")

            logger.info(f"[GENERATE_NAME] session={session_id} {llm_names}")
            # 6. 保存 name
            new_names = await NameOp.insert_names(session, llm_names)

        if new_names:
            for n in new_names:
                await session.refresh(n)
            return {"names": [n.model_dump() for n in new_names], "prompt": prompt if debug else None}
        else:
            return {"content": response, "prompt": prompt if debug else None}
