# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
from typing import List, Union, Optional

from fastapi import APIRouter, Depends, WebSocket
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from config.config import StyleSettings
from service.db import get_asession
from service.db.message_op import MessageOp
from service.db.name_op import NameOp
from service.format_utils import user_msg, assistant_msg
from service.goodname import GoodNameService
from service.llm_client import DeltaMessage
from service.middleware import LoggingWebRoute
from service.model import Message
from service.model.name import NameView

router = APIRouter(route_class=LoggingWebRoute)


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8090/api/goodname/ws/test_ws/name");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@router.get("/")
async def generate_names_ws():
    from fastapi.responses import HTMLResponse
    return HTMLResponse(html)

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

    @field_validator("style", mode="before")
    @classmethod
    def validate_style(cls, values):
        assert all([s in StyleSettings.all_styles for s in values]), \
            f"style only support {StyleSettings.all_styles}"
        return values


class NamesModel(BaseModel):
    names: Optional[List[NameView]] = None
    content: Optional[str] = None


@router.websocket("/ws/{session_id}/name")
async def generate_names_ws(
        websocket: WebSocket,
        *,
        session: AsyncSession = Depends(get_asession),
        session_id: str,
):
    await websocket.accept()

    while True:
        body = await websocket.receive_json()
        body = GenerateParam(**body)
        await generate_names(session=session, session_id=session_id, body=body, websocket=websocket)
        await websocket.send_json(DeltaMessage(type="completion", content="DONE").model_dump())


@router.post("/{session_id}/name",  response_model=NamesModel)
async def generate_names(
        *,
        session: AsyncSession = Depends(get_asession),
        session_id: str,
        body: GenerateParam,
        websocket: WebSocket = None # 本方法不支持流式，留给流式接口调用
):
    # 保存用户信息
    await MessageOp.insert_message(session, Message(**user_msg(body.query), styles=body.style, session_id=session_id))

    current_like_name = []
    for a in body.attachment:
        like = await NameOp.like_name_by_id(session, a.id)
        current_like_name.append(like)

    intention = await GoodNameService.check_and_intention(session=session, session_id=session_id)

    response = None
    # 异常情况
    if isinstance(intention, str):
        response = {"content": intention}
    # 没有姓名和性别情况
    elif intention.get("last_name") in [None, "", "无", "空"] or intention.get("gender") not in ["男孩", "女孩"]:
        response = {"content": intention.get("reply")}
    elif "生辰八字" in body.style and intention.get("birthdate") in [None, "", "无", "空"]:
        response = {"content": intention.get("reply")}
    elif "家族辈份" in body.style and intention.get("family_word") in [None, "", "无"]:
        response = {"content": intention.get("reply")}

    if response:
        if websocket:
            await websocket.send_json(DeltaMessage(type="message.delta", content=response.get("content")).model_dump())
    # 正常情况
    else:
        response = await GoodNameService.generate_names(
            session=session,
            last_name=intention["last_name"],
            gender=intention["gender"],
            birthdate=intention.get("birthdate"),
            family_word=intention.get("family_word"),
            session_id=session_id,
            user_id=body.user_id,
            styles=body.style,
            current_like_name=current_like_name,
            num=body.num,
            model=body.model,
            debug=body.debug,
            websocket=websocket,
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
