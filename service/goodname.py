# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
import random
from typing import List, Dict, Any, Union

from loguru import logger
from pypinyin import pinyin
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import WebSocket

from config.config import LLMSettings, StyleSettings
from service.const import LIKE
from service.db.message_op import MessageOp
from service.db.name_op import NameOp
from service.format_utils import user_msg, extract_json, system_msg, \
    format_messages, assistant_msg
from service.llm_client import ask_llm, DeltaMessage
from service.lunar_transfor import solar2lunar_chinese_str
from service.model import Name, Message
from service.model.name import NameCreate
from service.model.params import BasicInfo
from service.prompts import PromptFactory


class GoodNameService:

    @staticmethod
    async def check_and_intention(
            session: AsyncSession,
            session_id: str,
            basic_info: BasicInfo = None,
            model: str = "deepseek-v3"
    ) -> Union[BasicInfo, str]:
        history = await MessageOp.query_message_by_session_id(session=session, session_id=session_id)
        prompt = PromptFactory.format_template(prompt_name="intention_prompt", messages=history, context=basic_info)
        response = await ask_llm(
            model=LLMSettings.get_model(model),
            messages=[user_msg(prompt)],
        )
        intention = extract_json(response.content)
        if isinstance(intention, str):
            return intention
        elif isinstance(intention, dict):
            if not basic_info:
                return BasicInfo(**intention)
            else:
                return BasicInfo(**{**basic_info.model_dump(), **intention})
        else:
            raise TypeError(f"Intention must be str or BasicInfo.")


    @classmethod
    async def generate_names(
            cls,
            session: AsyncSession,
            session_id: str,
            user_id: str,       # 没啥用，只是 name 中需要
            context: BasicInfo = BasicInfo(),
            current_like_name: List[Name] = [],
            model: str = "deepseek-v3",
            temperature: float = 1.0,
            num: int = 5,
            websocket: WebSocket = None,
            **kwargs
    ) -> Dict[str, Any]:
        # 1. 获取所有已经生成的名字
        names = await NameOp.query_name_by_session_id(session=session, session_id=session_id)
        like_names = [n for n in names if n.prefer == LIKE]
        unlike_names = list(await NameOp.query_name_by_session_id(session=session, session_id=session_id, is_valid=False))

        # 2. 获取所有历史对话信息
        history = await MessageOp.query_message_by_session_id(session=session, session_id=session_id)
        history = MessageOp.process_history(
            history, context=context, current_like_name=current_like_name,
            like_names=like_names, unlike_names=unlike_names, names=names
        )

        # 4. 获取选择的风格 Prompt
        if styles_map := StyleSettings.get_selected_styles(context.styles):
            if "生辰八字" in styles_map:
                if not context.birthdate:
                    return {"content": "请您提供出生日期"}
            prompt_type = f"style_{list(styles_map.values())[0]}"
        else:
            prompt_type = random.choice(["style_combine", "style_default", "style_artistic"])

        # 如果是生辰八字，则先返回生辰八字的五行信息，只有在流式的情况下才使用
        wuxing = None
        if websocket and "生辰八字" in context.styles:
            birth_prompt = PromptFactory.format_template(
                prompt_name="analysis_birthdate",
                birthdate=context.birthdate,
            )
            wuxing = await ask_llm(
                model=LLMSettings.get_model(model),
                messages=[user_msg(birth_prompt)],
                temperature=temperature,
                context=context,
                websocket=websocket,
            )
            # 保存信息
            await MessageOp.insert_message(session, Message(
                **assistant_msg(wuxing.content), context=context,
                session_id=session_id))
            await websocket.send_json(DeltaMessage(type="message.delta", content=wuxing.content).model_dump())

        system_prompt = PromptFactory.format_template(
            prompt_name=prompt_type,
            styles=context.styles,
            names=names,
            last_name=context.last_name,
            gender=context.gender,
            family_word=context.family_word,
            birthdate=context.birthdate,
            num=num
        )

        messages = [system_msg(system_prompt)] + format_messages(history)

        # 4. 调用大模型
        if not model:
            model = random.choice(["deepseek-v3"])
        response = await ask_llm(
            model=LLMSettings.get_model(model),
            messages=messages,
            temperature=temperature,
            context=context,
            websocket=websocket,
            shengchenbazi=f"{solar2lunar_chinese_str(context.birthdate) if '生辰八字' in  context.styles and context.birthdate else ''}\n{wuxing.content if wuxing else ''}".strip(),
        )

        # 5. 解析结果
        result = extract_json(response.content, r"\[.*\]")
        if isinstance(result, str):
            return {"content": response.content}
        else:
            new_names = []
            if result:
                had_names = []
                for r in result:
                    try:
                        if not r.get("name").startswith(context.last_name):
                            r["name"] = f"{context.last_name}{r['name']}"
                        if r.get("name") in had_names:
                            continue
                        if "生辰八字" in context.styles and context.birthdate:
                            r["shengchenbazi"] = f"{solar2lunar_chinese_str(context.birthdate)}\n{wuxing.content if wuxing else ''}".strip()
                        if "家族辈份" in context.styles and context.family_word:
                            r["family_word"] = context.family_word
                        r["styles"] = context.styles
                        r["gender"] = context.gender
                        r["pinyin"] = " ".join([p[0] for p in pinyin(r["name"])])
                        new_names.append(NameCreate(**r, last_name=context.last_name, session_id=session_id, user_id=user_id))
                        had_names.append(r["name"])
                    except Exception as e:
                        logger.warning(f"[SAVE_NAME] name={r} error={e}")

            logger.info(f"[GENERATE_NAME] session={session_id} {new_names}")
            # 6. 保存 name
            new_names = await NameOp.insert_names(session, new_names)

            for n in new_names:
                await session.refresh(n)
            return {"names": new_names}
