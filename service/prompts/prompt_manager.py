# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/22
# 
# ====================
from pathlib import Path

from jinja2 import FileSystemLoader, Environment
from pydantic import BaseModel

from config.books import Books
from service.lunar_transfor import solar2lunar_chinese_str


_DEFAULT = "style_default"


class _PromptFactory:

    def __init__(self):
        file_dir = str(Path(__file__).absolute().parent)
        _loader = FileSystemLoader(searchpath=file_dir)
        self._env = Environment(loader=_loader)
        self._env.globals["solar2lunar_chinese_str"] = solar2lunar_chinese_str
        self._env.globals["poetries"] = Books.random

    def format_template(self, prompt_name: str = _DEFAULT, **kwargs) -> str:
        if "num" not in kwargs:
            kwargs["num"] = 3
        for k, v in kwargs.items():
            if not v:
                kwargs[k] = None
            elif isinstance(v, BaseModel):
                kwargs[k] = v.model_dump()
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
