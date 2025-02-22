# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/9
# 
# ====================
from loguru import logger
import time
from typing import Callable, Coroutine, Any

from fastapi.routing import APIRoute
from fastapi import Request
from fastapi import Response


class LoggingWebRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        origin_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                start = time.time()
                logger.info(f"[REQUEST] method={request.method} path={request.url.path}")
                response = await origin_route_handler(request)
                logger.info(f"[RESPONSE] path={request.url.path} cost={time.time()-start} response={response.body}")
                return response
            except Exception as e:
                body = await request.body()
                logger.error(f"body={body}")
                raise e

        return custom_route_handler

