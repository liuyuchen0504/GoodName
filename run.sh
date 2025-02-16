#!/bin/bash

uvicorn main:app --host 0.0.0.0 --port 8090 --workers 4

# 启动python 端口 7860
python ./app/app.py
