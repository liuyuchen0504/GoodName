# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
from typing import Optional, List, Dict, Any

from pydantic import computed_field, BaseModel
from sqlalchemy import UniqueConstraint, Column, JSON, Index, Enum
from sqlmodel import SQLModel, Field

from service.const import PREFER_TYPE
from service.model.utils import TimestampMixin


class NameBase(BaseModel):
    name: str = Field(description="姓名")
    last_name: str = Field(description="姓氏")
    pinyin: Optional[str] = Field(default=None, description="名字拼音")
    gender: Optional[str] = Field(default="未知", include=["未知", "男孩", "女孩"], description="性别")
    meaning: Optional[str] = Field(default=None, description="寓意")
    shengchenbazi: Optional[str] = Field(default=None, description="生辰八字")
    family_word: Optional[str] = Field(default=None, description="家族辈份")
    # 风格
    styles: Optional[List[str]] = Field(default=[], sa_column=Column(JSON))
    is_star: Optional[bool] = Field(default=False, description="收藏")

    def __str__(self):
        name_str = self.name
        if self.meaning:
            name_str += f"：{self.meaning}"
        return name_str


class Name(NameBase, TimestampMixin, table=True):
    __tablename__ = "name"

    __table_args__ = (
        UniqueConstraint("session_id", "name", name="unique_session_id_name"),
        Index("name_idx", "name"),
        Index("gender_idx", "gender"),
        Index("user_id_idx", "user_id"),
        Index("name_session_id_idx", "session_id"),
        Index("is_valid_idx", "is_valid"),
        Index("prefer_idx", "prefer"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str        # 标识用户
    session_id: str     # 标识会话，目前可以使用 user_id

    is_valid: Optional[bool] = Field(default=True)
    prefer: str = Field(default="unknown", sa_column=Column(Enum(*PREFER_TYPE)))

    def to_dict(self):
        feature_dct = {
            "name": self.name,
            "meaning": self.meaning
        }
        return feature_dct


class NameCreate(NameBase):
    user_id: str  # 标识用户
    session_id: str  # 标识会话，目前可以使用 user_id


class NameView(NameBase):
    """View"""

    id: int

    @computed_field
    @property
    def feature(self) -> List[Dict[str, Any]]:
        feat = []
        if self.shengchenbazi:
            feat.append({"生辰八字": self.shengchenbazi})
        if self.family_word:
            feat.append({"家族辈份": self.family_word})
        return feat
