# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
from typing import Optional, Sequence, List

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from service.const import UNLIKE, LIKE
from service.model.name import Name, NameCreate


class NameOp:

    @classmethod
    async def insert_names(
            cls, session: AsyncSession,
            names: List[NameCreate]
    ):
        if not names:
            return []
        session_id = names[0].session_id
        db_names = await cls.query_name_by_condition(session, session_id=session_id)
        db_names = [d.name for d in db_names]
        name_entity = []
        for n in names:
            if n.name in db_names:
                logger.warning(f"[NAME_REPEAT] session={session_id} name={n.name}")
                continue
            entity = Name(**n.model_dump())
            name_entity.append(entity)
            session.add(entity)
        await session.commit()
        for n in name_entity:
            await session.refresh(n)
        logger.info(f"[InsertNames] session={names[0].session_id} names={[n.name for n in name_entity]}")
        return name_entity


    @classmethod
    async def query_name_by_condition(
            cls, session: AsyncSession,
            name_id: str = None,
            user_id: str = None,
            session_id: str = None,
            is_valid: bool = True,
            prefer: Optional[List[str]] = None,
            limit: int = 0
    ) -> Sequence[Name]:
        assert name_id or session_id

        statement = select(Name)
        if name_id:
            statement = statement.where(Name.id == name_id)
        if user_id:
            statement = statement.where(Name.user_id == user_id)
        if session_id:
            statement = statement.where(Name.session_id == session_id)
        if is_valid is not None:
            statement = statement.where(Name.is_valid == is_valid)
        if prefer:
            statement = statement.filter(Name.prefer.in_(prefer))
        if limit > 0:
            statement = statement.limit(limit=limit)
        return (await session.execute(statement)).scalars().all()

    @classmethod
    async def query_name_by_id(
            cls, session: AsyncSession,
            name_id: int,
    ) -> Optional[Name]:
        statement = select(Name).where(Name.id == name_id)
        return (await session.execute(statement)).scalars().one_or_none()


    @classmethod
    async def query_name_by_session_id(
            cls, session: AsyncSession,
            session_id: str,
            is_valid: bool = True,
            prefer: Optional[List[str]]=None,
            limit: int = 100,
    ) -> Sequence[Name]:
        return await cls.query_name_by_condition(session=session, session_id=session_id, is_valid=is_valid, prefer=prefer, limit=limit)

    @classmethod
    async def delete_name_by_id(
            cls, session: AsyncSession,
            name_id: int,
    ) -> Optional[Name]:
        name = await cls.query_name_by_id(session=session, name_id=name_id)
        if name:
            name.is_valid = False
            name.prefer = UNLIKE
            session.add(name)
            await session.commit()
            await session.refresh(name)
        return name

    @classmethod
    async def like_name_by_id(
            cls, session: AsyncSession,
            name_id: int,
    ) -> Optional[Name]:
        name = await cls.query_name_by_id(session=session, name_id=name_id)
        if name:
            name.prefer = LIKE
            session.add(name)
            await session.commit()
            await session.refresh(name)
        return name