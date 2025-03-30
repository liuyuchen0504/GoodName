# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
from typing import List, Union, Optional, Literal

from fastapi import APIRouter, Depends, WebSocket, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, update

from service.db import get_asession
from service.db.message_op import MessageOp
from service.db.name_op import NameOp
from service.db.paginate import paginate_query, PageResponse
from service.format_utils import user_msg
from service.goodname import GoodNameService
from service.llm_client import DeltaMessage
from service.middleware import LoggingWebRoute
from service.model import Message
from service.model.name import NameView, Name
from service.model.params import GenerateRequest, GenerateResponse

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
        if body.get("type") == "ping":
            await websocket.send_json(DeltaMessage(type="ping", content="DONE").model_dump())
            continue
        body = GenerateRequest(**body)
        await generate_names(session=session, session_id=session_id, body=body, websocket=websocket)
        await websocket.send_json(DeltaMessage(type="completion", content="DONE").model_dump())


@router.post("/{session_id}/name",  response_model=GenerateResponse)
async def generate_names(
        *,
        session: AsyncSession = Depends(get_asession),
        session_id: str,
        body: GenerateRequest,
        websocket: WebSocket = None # 本方法不支持流式，留给流式接口调用
):
    # 保存用户信息
    await MessageOp.insert_message(session, Message(**user_msg(body.query), context=body.context, session_id=session_id))

    current_like_name = []
    for a in body.attachment:
        like = await NameOp.like_name_by_id(session, a.id)
        current_like_name.append(like)

    intention = await GoodNameService.check_and_intention(session=session, session_id=session_id, basic_info=body.context)

    response = None
    # 异常情况
    if isinstance(intention, str):
        response = {"content": intention}
    # 没有姓名和性别情况
    elif intention.last_name in [None, "", "无", "空"] or intention.gender not in ["男孩", "女孩"]:
        response = {"content": intention.reply}
    elif "生辰八字" in body.context.styles and intention.birthdate in [None, "", "无", "空"]:
        response = {"content": intention.reply}
    elif "家族辈份" in body.context.styles and intention.family_word in [None, "", "无"]:
        response = {"content": intention.reply}

    if response:
        if websocket:
            await websocket.send_json(DeltaMessage(type="message.delta", content=response.get("content")).model_dump())
    # 正常情况
    else:
        response = await GoodNameService.generate_names(
            session=session,
            context=intention,
            session_id=session_id,
            user_id=body.user_id,
            current_like_name=current_like_name,
            num=body.num,
            model=body.model,
            websocket=websocket,
        )

    # 保存生成会话
    await MessageOp.insert_message(session, Message(
        role="assistant",
        content=response.get("content") or response.get("names"),
        content_type="text" if response.get("content") else "card",
        context=body.context,
        session_id=session_id))

    if names := response.get("names"):
        for n in names:
            await session.refresh(n)

    return response


@router.post("/{session_id}/collect")
async def collect_names(
        *,
        session: AsyncSession = Depends(get_asession),
        session_id: str,
        body: List[int],
):
    statement = update(Name).where(Name.id.in_(body)).values(is_star=True)
    await session.execute(statement)
    await session.commit()
    return {"code": 200, "message": "success"}


@router.get("/{session_id}/collect", response_model=PageResponse)
async def list_collect_names(
        *,
        session: AsyncSession = Depends(get_asession),
        session_id: str,
        page: int = Query(default=1, ge=0, description="页"),
        size: int = Query(10, gt=0, le=100, description="每页数量"),
        sort_by: Optional[str] = Query(None, description="排序字段"),
        order: Literal["asc", "desc"] = Query("asc", description="排序方式"),
) -> PageResponse[Name]:
    statement = select(Name).where(Name.session_id == session_id).where(Name.is_star == True)
    return await paginate_query(
        session=session,
        query=statement,
        table=Name,
        page=page,
        size=size,
        sort_by=sort_by,
        order=order
    )


@router.delete("/{session_id}/collect/{name_id}", response_model=Union[NameView, None])
async def cancel_collect(
        *,
        session: AsyncSession = Depends(get_asession),
        session_id: str,
        name_id: int
):
    statement = update(Name).where(Name.id == name_id).values(is_star=False)
    await session.execute(statement)
    await session.commit()
    await NameOp.query_name_by_id(session, name_id)
    return await NameOp.query_name_by_id(session, name_id)


@router.delete("/{session_id}/name/{name_id}", response_model=Union[NameView, None])
async def delete_name(
        *,
        session: AsyncSession = Depends(get_asession),
        session_id: str,
        name_id: int
):
    return await NameOp.delete_name_by_id(session=session, name_id=name_id)
