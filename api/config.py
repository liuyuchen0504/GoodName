# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
from typing import List, Optional, Dict, Any

from fastapi import APIRouter
from pydantic import BaseModel

from config.config import StyleSettings
from service.middleware import LoggingWebRoute
from service.model import Name

router = APIRouter(route_class=LoggingWebRoute)


@router.get("/style", response_model=List[Dict[str, Any]])
async def style():
    return [{"name": s} for s in StyleSettings.all_styles]


class SugRequest(BaseModel):
    attachment: Optional[List[Name]] = []


@router.post("/sug/{session_id}", response_model=List[str])
async def sug(*, session_id: str, body: SugRequest = None):
    if body and body.attachment:
        return [
            "这个名字还不错，请你在取一些类似的名字",
            "保留中间的字，再根据中间的字搭配取几个名字",
            "根据这个名字的寓意再取一些名字"
        ]
    else:
        return [
            "我希望我的女儿健康快乐",
            "我希望他是个阳光开朗大男孩",
            "我希望他未来健康、乐观"
        ]
