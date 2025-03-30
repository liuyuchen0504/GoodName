# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
import re
from typing import Sequence, Optional, Literal, List

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from service.db.paginate import paginate_query, PageResponse
from service.model import Message, Name
from service.model.message import MessageBase
from service.model.name import NameBase
from service.model.params import BasicInfo


class MessageOp:

    @classmethod
    async def query_message_by_session_id(
            cls, session: AsyncSession,
            session_id: str,
            limit: int = 0,
    ) -> Sequence[Message]:
        statement = select(Message).where(Message.session_id == session_id)
        if limit > 0:
            statement = statement.limit(limit=limit)
        return (await session.execute(statement)).scalars().all()

    @classmethod
    async def insert_message(
            cls, session: AsyncSession,
            message: Message,
    ) -> Optional[Message]:
        session.add(message)
        await session.commit()
        await session.refresh(message)
        logger.info(f"[InsertMessage] message={message}")
        return message

    @classmethod
    async def query_message_by_session_id_paginate(
            cls, session: AsyncSession,
            session_id: str,
            page: int = 0,
            size: int = 10,
            sort_by: Optional[str] = None,
            order: Literal["asc", "desc"] = "asc",
    ) -> PageResponse[Message]:
        statement = select(Message).where(Message.session_id == session_id)
        return await paginate_query(
            session=session,
            query=statement,
            table=Message,
            page=page,
            size=size,
            sort_by=sort_by,
            order=order
        )

    @staticmethod
    def process_history(
            messages: List[Message],
            context: BasicInfo,
            current_like_name: List[Name]=None,
            like_names: List[Name]=None,
            unlike_names: List[Name]=None,
            names: List[Name] = None,
            **kwargs) -> List[Message]:
        messages = [MessageBase(**msg.model_dump()) for msg in messages]
        # 诗词典籍 不能出现姓名相关的词，不然模型会陷入固有模式，因此不用历史消息
        if "诗词典籍" in context.styles:
            messages = messages[-1:]
        for message in messages:
            format_message(message, context, current_like_name, like_names, unlike_names, names, **kwargs)
        return messages


def format_message(
        message: MessageBase,
        context: BasicInfo,
        current_like_name: List[Name]=None,
        like_names: List[Name]=None,
        unlike_names: List[Name]=None,
        names: List[Name] = None,
        **kwargs
) -> Message:
    if '诗词典籍' in context.styles:
        # 去掉姓氏，姓氏会有影响
        current_like_name = _remove_last_name(current_like_name)
        like_names = _remove_last_name(like_names)
        unlike_names = _remove_last_name(unlike_names)
        names = _remove_last_name(names)

        if message.role == "user":
            if context.reply not in [None, "", "无"]:
                message.content = context.reply
            if current_like_name:
                message.content = f"针对此意象：{str(current_like_name[0])}\n\n{message.content}"
            names = [n for n in names if re.match(r".*『(.*)』.*", n.meaning)]
            if names:
                names_format = ""
                for n in names:
                    # 只添加那些引用正常的名字
                    if m := re.match(r".*『(.*)』.*", n.meaning):
                        if all([w in m.group(1) for w in n.name]):
                            names_format += f"\n{str(n)}"
                if names_format:
                    message.content += f"\n\n已经提供了以下这些意象，请不要重复提供：\n{names_format}"
        else:
            if message.content_type == "card":
                # 去掉姓氏，姓氏会有影响
                message.content = _remove_last_name(message.content)
    else:
        if message.role == "user":
            if current_like_name:
                message.content = f"\n请你针对如下姓名：\n{current_like_name}\n{message.content}"
    return message


def _remove_last_name(names: Optional[List[Name]]) -> Optional[List[NameBase]]:
    if not names:
        return names
    names = [NameBase(**name.model_dump()) for name in names]
    for name in names:
        name.name = name.name.replace(name.last_name, "")
    return names
