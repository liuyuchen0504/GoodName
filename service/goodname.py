# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
import random
from typing import List, Dict, Any

from loguru import logger
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import WebSocket

from config.config import LLMSettings, StyleSettings
from service.const import LIKE
from service.db.message_op import MessageOp
from service.db.name_op import NameOp
from service.format_utils import user_msg, extract_json, system_msg, format_messages
from service.llm_client import ask_llm
from service.lunar_transfor import solar2lunar_chinese_str
from service.model import Name
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
        prompt = PromptFactory.format_template(prompt_name="intention_prompt", messages=history)
        response = await ask_llm(
            model=LLMSettings.get_model(model),
            messages=[user_msg(prompt)],
        )
        return extract_json(response.content)


    @classmethod
    async def generate_names(
            cls,
            session: AsyncSession,
            session_id: str,
            user_id: str,       # 没啥用，只是 name 中需要
            last_name: str = None,
            gender: str = None,
            birthdate: str = None,
            family_word: str = None,
            style: List[str] = [],
            current_like_name: List[Name] = [],
            model: str = "deepseek-v3",
            temperature: float = 1.0,
            num: int = 5,
            websocket: WebSocket = None,
            debug: bool = False,
            **kwargs
    ) -> Dict[str, Any]:
        # 1. 获取所有已经生成的名字
        names = await NameOp.query_name_by_session_id(session=session, session_id=session_id)
        like_names = [n for n in names if n.prefer == LIKE]
        unlike_names = list(await NameOp.query_name_by_session_id(session=session, session_id=session_id, is_valid=False))

        # 2. 获取所有历史对话信息
        history = await MessageOp.query_message_by_session_id(session=session, session_id=session_id)

        # 3. 获取选择的风格，目前只支持单风格
        styles = StyleSettings.get_selected_styles(style)

        # 4. Prompt
        if styles:
            if "生辰八字" in styles:
                if not birthdate:
                    return {"content": "请您提供出生日期"}
            prompt_type = f"style_{list(styles.values())[0]}"
        else:
            prompt_type = random.choice(["style_combine", "style_default", "style_artistic", "style_jinyong", "style_qiongyao"])
        system_prompt = PromptFactory.format_template(
            prompt_name=prompt_type,
            styles=styles,
            names=names,
            last_name=last_name,
            gender=gender,
            family_word=family_word,
            birthdate=birthdate,
            num=num
        )

        messages = [system_msg(system_prompt)] + format_messages(history)

        # 4. 调用大模型
        response = await ask_llm(
            model=LLMSettings.get_model(model),
            messages=messages,
            temperature=temperature,
            websocket=websocket,
        )

        # 5. 解析结果
        result = extract_json(response.content, r"\[.*\]")
        if isinstance(result, str):
            return {"content": response.content, "prompt": system_prompt if debug else None}
        else:
            llm_names = []
            if result:
                had_names = []
                for r in result:
                    try:
                        if r.get("name") in had_names:
                            continue
                        if "生辰八字" in styles and birthdate:
                            r["shengchengbazi"] = solar2lunar_chinese_str(birthdate)
                        llm_names.append(NameCreate(**r, session_id=session_id, user_id=user_id))
                        had_names.append(r["name"])
                    except Exception as e:
                        logger.warning(f"[SAVE_NAME] name={r} error={e}")

            logger.info(f"[GENERATE_NAME] session={session_id} {llm_names}")
            # 6. 保存 name
            new_names = await NameOp.insert_names(session, llm_names)

            for n in new_names:
                await session.refresh(n)
            return {"names": new_names, "prompt": system_prompt if debug else None}
