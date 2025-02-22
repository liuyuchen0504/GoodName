# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/22
# 
# ====================
import os
from pathlib import Path
from typing import Dict

from jinja2 import Template
from pydantic import BaseModel


class _PromptFactory:

    def __init__(self):
        file_dir = str(Path(__file__).absolute().parent)

        self._templates: Dict[str, Template] = {}
        for f in os.listdir(file_dir):
            if f.endswith(".jj2"):
                with open(os.path.join(file_dir, f)) as rf:
                    self._templates[f[:-4]] = Template("".join(rf.readlines()))

        print(self._templates)

    def format_template(self, prompt_name: str = "good_name_prompt_v1", user_prompt: str = None, trans_str: bool = False, **kwargs):
        if trans_str:
            prompt_name += "_debug"
        if "num" not in kwargs:
            kwargs["num"] = 3
        for k, v in kwargs.items():
            if not v:
                kwargs[k] = None
            elif isinstance(v, BaseModel):
                kwargs[k] = v.model_dump()
            if trans_str:
                kwargs[k] = self.object_2_string(v)
        return (user_prompt or self._templates[prompt_name]).render(**kwargs)

    @staticmethod
    def object_2_string(data):
        if not data:
            return ""
        if isinstance(data, str):
            return data
        elif isinstance(data, dict):
            return "\n".join([f"  - {k}：{v}" for k, v in data.items() if k and v])
        elif isinstance(data, list):
            return "\n".join([f"  - {d}" for d in data if d])
        elif isinstance(data, BaseModel):
            return "\n".join([f"  - {k}：{v}" for k, v in data.model_dump().items() if k and v])
        # 其他类型不处理
        else:
            return data




PromptFactory = _PromptFactory()


if __name__ == "__main__":
    styles = {"金庸风": "xxx", "琼瑶风": "xxx"}
    messages = [{"role": "user", "content": "你好"}, {"role": "assistant", "content": "你姓什么"}, {"role": "user", "content": "姓刘"}]
    like_names = [{"name": "刘晓生", "meaning": "xxx"}, {"name": "刘晓生", "meaning": "xxx"}]
    unlike_names = None #[{"name": "刘晓生", "meaning": "xxx"}, {"name": "刘晓生", "meaning": "xxx"}]
    current_like_name = {"name": "刘晓生", "meaning": "xxx"}
    print(PromptFactory.format_template(
        "good_name_prompt_v1",
        styles=styles,
        messages=messages,
        like_names=like_names,
        unlike_names=unlike_names,
        current_like_name=current_like_name,
    ))
