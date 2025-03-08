# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
from typing import Optional, List, Dict, Any

from pydantic import computed_field
from sqlalchemy import UniqueConstraint, Column, JSON, Index, Enum
from sqlmodel import SQLModel, Field

from service.const import PREFER_TYPE
from service.model.utils import TimestampMixin


class NameBase(SQLModel):
    name: str
    pinyin: Optional[str] = Field(default=None, description="名字拼音")
    meaning: Optional[str] = Field(default=None, description="寓意")
    shengchengbazi: Optional[str] = Field(default=None, description="生辰八字")
    wuxingbagua: Optional[str] = Field(default=None, description="五行八卦")
    jiazubeifen: Optional[str] = Field(default=None, description="家族辈份")
    # 风格
    style: Optional[List[str]] = Field(default=[],
                                       sa_column=Column("style", JSON))


class Name(NameBase, TimestampMixin, table=True):
    __tablename__ = "name"

    __table_args__ = (
        UniqueConstraint("session_id", "name", name="unique_session_id_name"),
        Index("name_idx", "name"),
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

    def __str__(self):
        name_str = self.name
        if self.pinyin:
            name_str += f"（{self.pinyin}）"
        if self.meaning:
            name_str += f"：表达了{self.meaning}"
        return name_str

    def to_dict(self):
        return {
            "name": self.name,
            "pinyin": self.pinyin,
            "meaning": self.meaning
        }


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
        if self.shengchengbazi:
            feat.append({"生成八字": self.shengchengbazi})
        if self.wuxingbagua:
            feat.append({"五行八卦": self.wuxingbagua})
        if self.jiazubeifen:
            feat.append({"家族辈份": self.jiazubeifen})
        return feat
