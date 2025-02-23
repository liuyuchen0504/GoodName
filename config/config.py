# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/9
# 
# ====================
import json
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
    GRADIO_PORT: int


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
        style_path = str(Path(__file__).absolute().parent.parent / "service/prompts/style_prompt.json")
        with open(style_path, "rb") as rf:
            self._styles = json.load(rf)

    def get_selected_styles(self, styles: List[str], user_style_prompts: Dict[str, str] = None):
        if not styles:
            return None
        return {k: v for k, v in (user_style_prompts or self._styles).items() if k in styles}

    @property
    def all_styles(self):
        return list(self._styles.keys())


StyleSettings = _StyleSettings()
