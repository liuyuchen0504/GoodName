# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
from fastapi import APIRouter

from service.middleware import LoggingWebRoute


router = APIRouter(route_class=LoggingWebRoute)


@router.get("/style")
async def style():
    return [
        {"name": "生辰八字"},
        {"name": "五行八卦"},
        {"name": "家族辈份"},
        {"name": "金庸风"},
        {"name": "琼瑶风"},
        {"name": "文艺风"},
    ]



@router.get("/sug")
async def sug():
    return [
        "我希望我的女儿健康快乐",
        "我希望他是个阳光开朗大男孩",
        "我希望他未来健康、乐观"
    ]



