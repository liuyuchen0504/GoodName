# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/9
# 
# ====================
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class EnvBaseSettings(BaseSettings):
    class Config:
        env_file = str(Path(__file__).absolute().parent / "config.prod")
        extra = "allow"


class _APPSettings(EnvBaseSettings):
    HOST: str
    PORT: int


class _LLMSettings(EnvBaseSettings):
    BASE_URL: str
    API_KEY: str

    MODEL: str


APPSettings = _APPSettings()
LLMSettings = _LLMSettings()


class StyleSettings:

    _styles = {
        "金庸风": "取的名字要和金庸武侠中正面人物的名字风格类似，但是不用直接使用金庸武侠人物的名字，比如：不能直接取风清扬，但可以任逍遥，两者都有潇洒的感觉"
    }

    @classmethod
    def get_style_prompt(cls, style: str, default: str=None):
        return cls._styles.get(style, default)

    @classmethod
    def format_styles_prompt(cls, styles: List[str], default: str=None):
        if not styles:
            return "无"
        style_prompts = [cls._styles.get(s, default) for s in styles]
        style_prompts = [s for s in style_prompts if s]
        return "\n".join([f"- {s}" for s in style_prompts]) if style_prompts else "无"
