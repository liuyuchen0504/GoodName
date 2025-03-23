# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/3/23
# 
# ====================
from typing import List, Optional, Literal, TypeVar, Generic

from pydantic import Field, computed_field, BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, select, func, asc, desc


T = TypeVar("T")


class PageResponse(BaseModel, Generic[T]):
    items: List[T] = Field([], description="数据")
    total: int = Field(description="总数")
    page: int = Field(description="页码")
    size: int = Field(description="条数")
    pages: int = Field(description="总页数")

    @computed_field
    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @computed_field
    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @computed_field
    @property
    def next_page(self) -> Optional[int]:
        return self.page + 1 if self.has_next else None

    @computed_field
    @property
    def prev_page(self) -> Optional[int]:
        return self.page - 1 if self.has_prev else None


async def paginate_query(
        session: AsyncSession,
        query,                  # SQLModel 的 sql 表达式
        table: SQLModel,
        page: int = 1,
        size: int = 10,
        sort_by: str = None,
        order: Literal["asc", "desc"] = "asc",
) -> PageResponse:
    if sort_by:
        direction = asc if order == "asc" else desc
        query = query.order_by(direction(getattr(table, sort_by)))
    total = (await session.execute(select(func.count()).select_from(query.subquery()))).scalar()
    pages = (total + size - 1) // size
    items = (await session.execute(query.offset((page - 1) * size).limit(size))).scalars().all()
    result = PageResponse[table](
        total=total,
        page=page,
        size=size,
        pages=pages,
    )
    result.items = items
    return result

