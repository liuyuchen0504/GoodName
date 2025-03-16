# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
import json
from typing import Optional, List

from sqlalchemy import Column, Index, Enum, JSON
from sqlmodel import SQLModel, Field

from service.const import MESSAGE_TYPE
from service.model.utils import TimestampMixin


class MessageBase(SQLModel):
    class Config:
        json_dumps = lambda x: x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)

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
    styles: List[str] = Field(default=None, sa_column=Column("styles", JSON))

    def __str__(self):
        return f"{self.role}: {self.content}"

    def __repr__(self):
        return self.__str__()
