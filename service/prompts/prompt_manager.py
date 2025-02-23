# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/22
# 
# ====================
from pathlib import Path

from jinja2 import Template, FileSystemLoader, Environment
from pydantic import BaseModel

from service.model import Message


class _PromptFactory:

    def __init__(self):
        file_dir = str(Path(__file__).absolute().parent)
        _loader = FileSystemLoader(searchpath=file_dir)
        self._env = Environment(loader=_loader)

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
        if user_prompt:
            # 补充输出格式要求
            user_prompt += "{%- extends './output_format.jj2' -%}\n{%- block output %}\n{{super()}}\n{%- endblock -%}"
            template = self._env.from_string(user_prompt)
        else:
            template = self._env.get_template(f"{prompt_name}.jj2")
        return template.render(**kwargs)

    @staticmethod
    def object_2_string(data):
        if not data:
            return ""
        if isinstance(data, str):
            return data
        elif isinstance(data, dict):
            return "\n".join([f"  - {k}：{v}" for k, v in data.items() if k and v])
        elif isinstance(data, list):
            return "\n".join([f"  - {str(d)}" for d in data if d])
        elif isinstance(data, BaseModel):
            return "\n".join([f"  - {k}：{v}" for k, v in data.model_dump().items() if k and v])
        # 其他类型不处理
        else:
            return data


PromptFactory = _PromptFactory()


if __name__ == "__main__":
    styles = {"金庸风": "xxx", "琼瑶风": "xxx"}
    messages = [Message(**{"role": "user", "content": "你好"}), Message(**{"role": "assistant", "content": "你姓什么"}), Message(**{"role": "user", "content": "姓刘"})]
    like_names = [{"name": "刘晓生", "meaning": "xxx"}, {"name": "刘晓生", "meaning": "xxx"}]
    unlike_names = None #[{"name": "刘晓生", "meaning": "xxx"}, {"name": "刘晓生", "meaning": "xxx"}]
    current_like_name = {"name": "刘晓生", "meaning": "xxx"}
    print(PromptFactory.format_template(
        "good_name_prompt_v1",
        trans_str=True,
        styles=styles,
        messages=messages,
        like_names=like_names,
        unlike_names=unlike_names,
        current_like_name=current_like_name,
    ))
