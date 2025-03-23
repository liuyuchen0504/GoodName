# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
from typing import Optional, Literal

from sqlmodel import Column, Index, Enum, JSON
from sqlmodel import SQLModel, Field

from service.const import MESSAGE_TYPE
from service.model.name import NameView
from service.model.params import BasicInfo, BasicInfoType
from service.model.utils import TimestampMixin


class MessageBase(SQLModel):
    role: str = Field(sa_column=Column(Enum(*MESSAGE_TYPE)))
    content: str = Field(description="消息内容", sa_column=Column(JSON))
    content_type: Literal["text", "card"] = Field(default="text", sa_column=Column(Enum("text", "card")))


class Message(MessageBase, TimestampMixin, table=True):
    __tablename__ = "message"

    __table_args__ = (
        Index("message_session_id_idx", "session_id"),
        Index("created_at_idx", "created_at"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str
    context: BasicInfo = Field(default=BasicInfo(), sa_column=Column(BasicInfoType))
    attachment: Optional[NameView] = Field(default=None, sa_column=Column(JSON))

    def __str__(self):
        return f"{self.role}: {self.content}"

    def __repr__(self):
        return self.__str__()
