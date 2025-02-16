# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
from typing import List, Union, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from service.db import get_asession
from service.db.name_op import NameOp
from service.goodname import GoodNameService
from service.middleware import LoggingWebRoute
from service.model.name import NameView

router = APIRouter(route_class=LoggingWebRoute)



@router.get("/{session_id}/name", response_model=List[Union[NameView, None]])
async def list_names(
        *,
        session: AsyncSession = Depends(get_asession),
        session_id: str,
        is_valid: bool = True,
        limit: int = 100,
):
    return await NameOp.query_name_by_session_id(session=session, session_id=session_id, is_valid=is_valid, limit=limit)


class GenerateParam(BaseModel):
    user_id: str
    query: str
    style: List[str] = []
    attachment: Optional[List[NameView]] = []


@router.post("/{session_id}/name",  response_model=List[Union[NameView, None]])
async def generate_names(
        *,
        session: AsyncSession = Depends(get_asession),
        session_id: str,
        body: GenerateParam,
):
    current_like_name = []
    for a in body.attachment:
        like = await NameOp.like_name_by_id(session, a.id)
        current_like_name.append(like)
    return await GoodNameService.generate_names(
        session=session,
        query=body.query,
        session_id=session_id,
        user_id=body.user_id,
        style=body.style,
        current_like_name=current_like_name,
    )


@router.delete("/{session_id}/name/{name_id}", response_model=Union[NameView, None])
async def delete_name(
        *,
        session: AsyncSession = Depends(get_asession),
        session_id: str,
        name_id: int
):
    return await NameOp.delete_name_by_id(session=session, name_id=name_id)
