# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
from pathlib import Path
from typing import AsyncGenerator, Callable

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlmodel import create_engine

DB_DIR = str(Path(__file__).absolute().parent)


engine = create_engine(f"sqlite:///{DB_DIR}/goodname.db")

aengine = create_async_engine(f"sqlite+aiosqlite:///{DB_DIR}/goodname.db")


session = scoped_session(sessionmaker(bind=engine))


# 创建session元类
asession_local: Callable[..., AsyncSession] = sessionmaker(
    bind=aengine,
    class_=AsyncSession,
)


async def get_asession() -> AsyncGenerator[AsyncSession, None]:
    async with asession_local() as session:
        yield session

