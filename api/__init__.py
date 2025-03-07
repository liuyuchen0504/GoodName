# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/9
# 
# ====================
from fastapi import APIRouter
from api import config
from api import goodname

api_router = APIRouter(prefix="/api")


api_router.include_router(config.router, prefix="/config", tags=["config"])
api_router.include_router(goodname.router, prefix="/goodname", tags=["goodname"])

