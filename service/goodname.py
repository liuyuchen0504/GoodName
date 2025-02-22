# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
from typing import List, Optional, Dict, Any

from loguru import logger
from sqlmodel.ext.asyncio.session import AsyncSession

from config.config import LLMSettings, StyleSettings
from service.const import LIKE
from service.db.message_op import MessageOp
from service.db.name_op import NameOp
from service.format_utils import user_msg, extract_json, assistant_msg
from service.llm_client import ask_llm
from service.model import Name, Message
from service.model.name import NameCreate
from service.prompts import PromptFactory


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
            debug: bool = False,
    ) -> Dict[str, Any]:
        # 0. 保存用户信息
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
        prompt = PromptFactory.format_template(
            "good_name_prompt_v1",
            user_prompt=system_prompt,
            styles=styles,
            messages=history,
            like_names=like_names,
            unlike_names=unlike_names,
            current_like_name=current_like_name,
            trans_str=debug,
        )

        messages = [user_msg(prompt)]

        # 4. 调用大模型
        response = ask_llm(
            model=LLMSettings.get_model(model),
            messages=messages,
            temperature=temperature,
        )

        # 5. 解析结果
        result = extract_json(response)
        new_names = None
        if isinstance(result, str):
            # 没有生成名字，返回交互文本
            content = result
        else:
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

            logger.info(f"[GENERATE_NAME] session={session_id} {llm_names}")
            # 6. 保存 name
            new_names = await NameOp.insert_names(session, llm_names)
            content = f"给您取了如下名字：{'，'.join([n.name for n in new_names])}" if new_names else "没有新的姓名"

        # 7 保存生成会话
        await MessageOp.insert_message(session, Message(**assistant_msg(content), session_id=session_id))

        if new_names:
            for n in new_names:
                await session.refresh(n)
            return {"names": new_names, "prompt": prompt if debug else None}
        else:
            return {"content": content, "prompt": prompt if debug else None}

