# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/3/9
# 
# ====================
from typing import Dict, Any

from pydantic import BaseModel


class Card(BaseModel):
    type: str
    data: Dict[str, Any]


class NameCard(Card):
    type: str = "name"
