# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/16
# 
# ====================
import asyncio
import json

import gradio as gr

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).absolute().parent.parent))

from config.config import APPSettings, StyleSettings
from service.db.name_op import NameOp
from service.db import asession_local
from service.goodname import GoodNameService


SYSTEM_PROMPT = """你是一个中国古诗词研究专家，精通韵律和典故。现在需要你按照用户的要求取名字。

## 取名规则
- 从历史对话中推断出用户姓氏，如果没有提供姓氏则让用户先提供姓氏
- 名字需要和姓氏相匹配：如姓杜不能叫杜子腾（谐音肚子疼）
- 名字要有好的寓意，要求是从四书五经、唐诗宋词等古典书籍中摘出的好字词：如张自强（取自天行健、君子以自强不息中的自强）
- 名字不要用著名的历史人物：如秦桧、赵高等臭名昭著反面人物，李世民、杜甫等明君直臣
- 名字不要用网上流行的一些网红名字：如子涵、紫萱、若曦、宇轩等之类的名字
- 一定要注意音律，名字叫起来朗朗上口
- 一次给出 {{num}} 个名字，给出名字、寓意、音律解释

## 取名要求
- 音律要求
    - 发音流畅，避免拗口。比如不要都是闭口音、不要两个三声声调的
    - 避免不好的谐音。比如王沙壁，沙壁和傻逼谐音，傻逼是骂人的
    - 要有韵律感，声调有起伏。如平仄平、仄平仄
    - 轻读和重读搭配

- 字形要求
    - 不要取笔画太多的字，不利于书写
    - 不要使用生僻字

- 风格要求
{{style}}

## 历史对话
{{messages}}

## 用户偏好
- 喜欢的名字
{{like_names}}

- 用户不喜欢的名字
{{unlike_names}}

- 用户当前满意的名字
{{current_like_name}}

根据历史对话总结用户需求，以及根据用户偏好取名字，尤其要关注用户当前满意的名字。禁止再给用户提供上述已经出现过的姓名
"""


#输入文本处理程序
def chat(session_id, prompt, style_prompt, model, temperature, style, query):
    if style_prompt:
        style_prompt = json.loads(style_prompt)
    params = {
        "query": query,
        "session_id": session_id,
        "user_id": session_id,
        "style": style or [],
        "model": model,
        "temperature": temperature,
        "system_prompt": prompt,
        "style_prompt": style_prompt,
        "debug": True,
    }

    history_names = asyncio.run(NameOp.query_name_by_session_id(session=asession_local(), session_id=session_id))

    rsps = asyncio.run(GoodNameService.generate_names(session=asession_local(), **params))
    names = rsps.get("names")
    content = rsps.get("content")
    prompt = rsps.get("prompt")
    if not names:
        return content, [], [[n.name, n.pinyin, n.meaning] for n in history_names], prompt
    return content, [[n.name, n.pinyin, n.meaning] for n in names], [[n.name, n.pinyin, n.meaning] for n in history_names], prompt


def main():
    # 定义输入
    session_box = gr.Text(lines=1, max_lines=1, value="test_session", label="Session")
    prompt_box = gr.Text(lines=6, max_lines=10, placeholder=SYSTEM_PROMPT, label="Prompt")
    style_prompt_box = gr.Text(lines=3, max_lines=4, placeholder="{\n  \"金庸风\": \"金庸武侠取名风格\"\n  \"琼瑶风\": \"琼瑶电视剧取名风格\"\n}", label="StylePrompt")
    model_box = gr.Radio(["deepseek-v3", "deepseek-r1", "doubao-1.5-pro-32k"], value="deepseek-v3", label="Model")
    temperature_box = gr.Slider(0, 1, value=1.0, step=0.1, info="值越高结果越随机，建议值：对话-1.3 创意-1.5", label="Temperature")
    # style_choice_box = gr.CheckboxGroup(StyleSettings.all_styles, label="Style")
    style_choice_box = gr.Dropdown(StyleSettings.all_styles, multiselect=True, label="Style")
    input_box = gr.Text(lines=1, placeholder="您对名字有什么要求", label="Input")
    output_text = gr.Text(lines=1, placeholder="返回信息", label="Content")
    output_history = gr.Dataframe(label="History", headers=["姓名", "拼音", "寓意"], datatype=["str", "str", "str"], interactive=False, max_height=300, wrap=True)
    output_df = gr.Dataframe(label="Name", headers=["姓名", "拼音", "寓意"], datatype=["str", "str", "str"], interactive=False, wrap=True)
    output_prompt = gr.Text(lines=4, max_lines=10, placeholder="LLM Input", label="LLM Prompt")
    demo = gr.Interface(
        fn=chat,           # 处理函数
        inputs=[session_box, prompt_box, style_prompt_box, model_box, temperature_box, style_choice_box, input_box],      # 定义输入
        outputs=[output_text, output_df, output_history, output_prompt],      # 定义输出
    )
    demo.launch(server_name=APPSettings.HOST, server_port=APPSettings.GRADIO_PORT, share=False)


if __name__ == "__main__":
    main()
