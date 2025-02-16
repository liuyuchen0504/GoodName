# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
from typing import List, Optional, Dict, Any

from fastapi import APIRouter
from pydantic import BaseModel

from service.middleware import LoggingWebRoute
from service.model import Name

router = APIRouter(route_class=LoggingWebRoute)


@router.get("/style", response_model=List[Dict[str, Any]])
async def style():
    return [
        {"name": "生辰八字"},
        {"name": "五行八卦"},
        {"name": "家族辈份"},
        {"name": "金庸风"},
        {"name": "琼瑶风"},
        {"name": "文艺风"},
    ]


class SugRequest(BaseModel):
    attachment: Optional[List[Name]] = []


@router.post("/sug/{session_id}", response_model=List[str])
async def sug(*, session_id: str, body: SugRequest = None):
    return [
        "我希望我的女儿健康快乐",
        "我希望他是个阳光开朗大男孩",
        "我希望他未来健康、乐观"
    ]



