# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/9
# 
# ====================
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import api_router
from config.config import APPSettings


def add_middleware(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )


def create_app():
    _app = FastAPI(title="GoodName")

    # 添加中间件
    add_middleware(_app)

    _app.include_router(api_router, prefix="")

    return _app


app = create_app()


@app.get("")
async def home():
    return "Welcome to GoodName APP!"



if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host=APPSettings.HOST,
        port=APPSettings.PORT
    )
