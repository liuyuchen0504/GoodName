#!/bin/bash

nohup uvicorn main:app --host 0.0.0.0 --port 8090 --workers 4 > nohup.log 2>&1 &

# 启动python 端口 7860
nohup python ./app/app.py > debug.log 2>&1 &
