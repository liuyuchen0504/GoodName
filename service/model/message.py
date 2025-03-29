# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
import json
import re
from typing import Optional, Literal, Union, List

from sqlalchemy import TypeDecorator
from sqlmodel import Column, Index, Enum, JSON
from sqlmodel import SQLModel, Field

from service.const import MESSAGE_TYPE
from service.model.name import NameView, Name
from service.model.params import BasicInfo, BasicInfoType
from service.model.utils import TimestampMixin


Content = Union[str, List[Name]]


class ContentType(TypeDecorator):
    impl = JSON  # 基于 SQLAlchemy 的 JSON 类型

    def process_bind_param(self, value, dialect):
        # 在写入数据库前将 BasicInfo 转为字典
        if isinstance(value, List):
            return [v.model_dump(exclude={"created_at", "updated_at"}) for v in value]
        return value

    def process_result_value(self, value, dialect):
        if not value:
            return value
        if isinstance(value, list):
            return [Name(**n) for n in value]
        elif re.match(r"\[.*\]", value, re.S):
            return [Name(**n) for n in json.loads(value)]
        else:
            return value


class MessageBase(SQLModel):
    role: str = Field(sa_column=Column(Enum(*MESSAGE_TYPE)))
    content: Content = Field(description="消息内容", sa_column=Column(ContentType))
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
