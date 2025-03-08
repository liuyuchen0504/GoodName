# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
from typing import List, Union, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from service.db import get_asession
from service.db.message_op import MessageOp
from service.db.name_op import NameOp
from service.format_utils import user_msg, assistant_msg
from service.goodname import GoodNameService
from service.middleware import LoggingWebRoute
from service.model import Message
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
    style: List[str] = Field([], description="风格")
    attachment: Optional[List[NameView]] = Field([], description="姓名卡片")
    num: int = Field(5, gt=0, description="名字数量")
    model: str = Field("deepseek-v3", description="模型")
    debug: bool = Field(False, description="是否 debug 模式")


class NamesModel(BaseModel):
    names: Optional[List[NameView]] = None
    content: Optional[str] = None


@router.post("/{session_id}/name",  response_model=NamesModel)
async def generate_names(
        *,
        session: AsyncSession = Depends(get_asession),
        session_id: str,
        body: GenerateParam,
):
    # 保存用户信息
    await MessageOp.insert_message(session, Message(**user_msg(body.query), session_id=session_id))

    current_like_name = []
    for a in body.attachment:
        like = await NameOp.like_name_by_id(session, a.id)
        current_like_name.append(like)

    intention = await GoodNameService.check_and_intention(session=session, session_id=session_id)

    # 异常情况
    if isinstance(intention, str):
        response = {"content": intention}
    # 没有姓名和性别情况
    elif intention.get("last_name") in [None, "", "无", "空"] or intention.get("sex") not in ["男孩", "女孩"]:
        response = {"content": intention.get("reply")}
    # 正常情况
    else:
        response = await GoodNameService.generate_names(
            session=session,
            query=body.query,
            last_name=intention["last_name"],
            sex=intention["sex"],
            session_id=session_id,
            user_id=body.user_id,
            style=body.style,
            current_like_name=current_like_name,
            num=body.num,
            model=body.model,
            debug=body.debug,
        )

    # 保存生成会话
    content = response.get("content") or [n.to_dict() for n in response.get("names")]
    await MessageOp.insert_message(session, Message(**assistant_msg(content), session_id=session_id))

    if names := response.get("names"):
        for n in names:
            await session.refresh(n)

    return response


@router.delete("/{session_id}/name/{name_id}", response_model=Union[NameView, None])
async def delete_name(
        *,
        session: AsyncSession = Depends(get_asession),
        session_id: str,
        name_id: int
):
    return await NameOp.delete_name_by_id(session=session, name_id=name_id)
