# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================

from typing import Optional

from sqlalchemy import Column, Index, Enum, JSON
from sqlmodel import SQLModel, Field

from service.const import MESSAGE_TYPE
from service.model.utils import TimestampMixin


class MessageBase(SQLModel):
    role: str = Field(sa_column=Column(Enum(*MESSAGE_TYPE)))
    content: str = Field(description="消息内容", sa_column=Column("content", JSON))



class Message(MessageBase, TimestampMixin, table=True):
    __tablename__ = "message"

    __table_args__ = (
        Index("message_session_id_idx", "session_id"),
        Index("created_at_idx", "created_at"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str

    def __str__(self):
        return f"{'用户' if self.role == 'user' else '助手'}：{self.content}"

    def __repr__(self):
        return self.__str__()
