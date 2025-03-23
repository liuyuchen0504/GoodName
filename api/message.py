# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
from typing import Optional, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from service.db import get_asession
from service.db.message_op import MessageOp
from service.db.paginate import PageResponse
from service.middleware import LoggingWebRoute
from service.model import Message

router = APIRouter(route_class=LoggingWebRoute)


@router.get("/{session_id}/message", response_model=PageResponse)
async def list_messages(
        *,
        session: AsyncSession = Depends(get_asession),
        session_id: str,
        page: int = Query(default=1, ge=0, description="页"),
        size: int = Query(10, gt=0, le=100, description="每页数量"),
        sort_by: Optional[str] = Query(None, description="排序字段"),
        order: Literal["asc", "desc"] = Query("asc", description="排序方式"),
) -> PageResponse[Message]:
    return await MessageOp.query_message_by_session_id_paginate(
        session=session, session_id=session_id, page=page, size=size,
        sort_by=sort_by, order=order
    )

