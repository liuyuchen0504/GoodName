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
        self._styles = {
            "生辰八字": "birthdate",
            "家族辈份": "lineage",
            "诗词典籍": "poetry",
            "文艺风": "artistic",
            "金庸风": "jinyong",
            "琼瑶风": "qiongyao",
        }

    def get_selected_styles(self, styles: List[str]):
        if not styles:
            return {}
        return {k: v for k, v in self._styles.items() if k in styles}

    @property
    def all_styles(self):
        return list(self._styles.keys())


StyleSettings = _StyleSettings()
