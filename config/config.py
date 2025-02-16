# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/9
# 
# ====================
from pathlib import Path
from typing import List, Optional, Dict

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

    ENDPIONT: Optional[str] = None

    _HUOSHAN_MODEL_MAPPING: Dict[str, str] = {
        "deepseek-r1": "ep-20250208203314-wqccp",
        "deepseek-v3": "ep-20250208203112-5kmc4",
        "doubao-1.5-pro-32k": "ep-20250208204913-l92d9",
    }

    def get_model(self, model: str):
        if self.ENDPIONT == "huoshan":
            return self._HUOSHAN_MODEL_MAPPING[model]
        else:
            return model



APPSettings = _APPSettings()
LLMSettings = _LLMSettings()


class _StyleSettings:

    def __init__(self):
        self._styles = {
            "金庸风": "取的名字要和金庸武侠中正面人物的名字风格类似，但是不用直接使用金庸武侠人物的名字，比如：不能直接取风清扬，但可以任逍遥，两者都有潇洒的感觉"
        }

    def format_styles_prompt(self, styles: List[str], default: str=None, user_style_prompts: Dict[str, str] = None):
        if not styles:
            return "无"
        style_prompts = [(user_style_prompts or self._styles).get(s, default) for s in styles]
        style_prompts = [s for s in style_prompts if s]
        return "\n".join([f"- {s}" for s in style_prompts]) if style_prompts else "无"

StyleSettings = _StyleSettings()
