# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
from typing import Sequence, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

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

