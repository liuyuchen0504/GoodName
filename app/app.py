# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/16
# 
# ====================
import asyncio

import gradio as gr

import sys
from pathlib import Path

from service.db.name_op import NameOp

sys.path.append(str(Path(__file__).absolute().parent.parent))

from service.db import asession_local
from service.goodname import GoodNameService


SYSTEM_PROMPT = """你是一个中国古诗词研究专家，精通韵律和典故。现在需要你按照用户的要求取名字。

## 风格要求
{style}

## 已取名字
{name}

## 用户喜欢的名字
{like_name}

## 用户不喜欢的名字
{not_like_name}

## 用户当前较满意的名字
{current_like_name}

请你务必注意必要再取上述已经有了的姓名，且不要取用户不喜欢的名字类似的名字
"""


#输入文本处理程序
def chat(session_id, prompt, style_prompt, model, temperature, style, query):

    params = {
        "query": query,
        "session_id": session_id,
        "user_id": session_id,
        "style": style or [],
        "model": model,
        "temperature": temperature,
        "system_prompt": prompt,
        "style_prompt": style_prompt,
    }

    history_names = asyncio.run(NameOp.query_name_by_session_id(session=asession_local(), session_id=session_id))

    names = asyncio.run(GoodNameService.generate_names(session=asession_local(), **params))
    if not names:
        return [], [[n.name, n.pinyin, n.meaning] for n in history_names]
    return [[n.name, n.pinyin, n.meaning] for n in names], [[n.name, n.pinyin, n.meaning] for n in history_names]



def main():
    # 定义输入
    session_box = gr.Text(lines=1, max_lines=1, value="test_session", label="Session")
    prompt_box = gr.Text(lines=6, max_lines=10, placeholder=SYSTEM_PROMPT, label="Prompt")
    style_prompt_box = gr.Text(lines=3, max_lines=4, placeholder="{\n  \"金庸风\": \"金庸武侠取名风格\"\n  \"琼瑶风\": \"琼瑶电视剧取名风格\"\n}", label="StylePrompt")
    model_box = gr.Radio(["deepseek-v3", "deepseek-r1", "doubao-1.5-pro-32k"], value="deepseek-v3", label="Model")
    temperature_box = gr.Slider(0, 2, value=1.0, step=0.1, info="值越高结果越随机，建议值：对话-1.3 创意-1.5", label="Temperature")
    style_choice_box = gr.CheckboxGroup(["金庸风", "琼瑶风"], label="Style")
    input_box = gr.Text(lines=1, placeholder="您对名字有什么要求", label="Input")
    output_history = gr.Dataframe(label="History", headers=["姓名", "拼音", "寓意"], datatype=["str", "str", "str"], interactive=False, wrap=True)
    output_df = gr.Dataframe(label="Name", headers=["姓名", "拼音", "寓意"], datatype=["str", "str", "str"], interactive=False, wrap=True)
    demo = gr.Interface(
        fn=chat,           # 处理函数
        inputs=[session_box, prompt_box, style_prompt_box, model_box, temperature_box, style_choice_box, input_box],      # 定义输入
        outputs=[output_df, output_history],      # 定义输出
    )
    demo.launch(share=True)


if __name__ == "__main__":
    main()
