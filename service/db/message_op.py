# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
from typing import Sequence, Optional, Literal

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from service.db.paginate import paginate_query, PageResponse
from service.model import Message


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
