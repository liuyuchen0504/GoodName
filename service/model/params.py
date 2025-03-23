# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/3/22
# 
# ====================
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import TypeDecorator, JSON

from config.config import StyleSettings
from service.model.name import NameView


class BasicInfoType(TypeDecorator):
    impl = JSON  # 基于 SQLAlchemy 的 JSON 类型

    def process_bind_param(self, value, dialect):
        # 在写入数据库前将 BasicInfo 转为字典
        if isinstance(value, BasicInfo):
            return value.model_dump()
        return value

    def process_result_value(self, value, dialect):
        # 从数据库读取时将字典转为 BasicInfo 实例（可选）
        if value is not None:
            return BasicInfo(**value)
        return value


class BasicInfo(BaseModel):
    """取名字需要的基础信息"""

    gender: Optional[str] = Field(default=None, description="性别")
    last_name: Optional[str] = Field(default=None, description="姓氏")
    birthdate: Optional[str] = Field(default=None, description="出生日期")
    family_word: Optional[str] = Field(default=None, description="家族辈份")
    styles: Optional[List[str]] = Field(default=[], description="风格")

    reply: Optional[str] = Field(default="", description="回复内容")

    @field_validator("styles", mode="before")
    @classmethod
    def validate_style(cls, values):
        assert all([s in StyleSettings.all_styles for s in values]), \
            f"style only support {StyleSettings.all_styles}"
        return values

    def __bool__(self):
        return bool(self.last_name or self.gender or self.birthdate or self.family_word or self.styles)

    def __str__(self):
        info = ""
        if self.last_name:
            info += f"姓氏：{self.last_name}"
        if self.gender:
            info += f"性别：{self.gender}"
        if self.birthdate:
            info += f"出生日期：{self.birthdate}"
        if self.family_word:
            info += f"家族辈份：{self.family_word}"
        # if self.styles:
        #     info += f"风格要求：{self.styles}"
        return info

    def __repr__(self):
        return str(self)


class GenerateRequest(BaseModel):
    user_id: str
    query: str

    context: BasicInfo = Field(default=BasicInfo(), description="所需要的基础信息")
    attachment: Optional[List[NameView]] = Field([], description="姓名卡片")
    num: int = Field(5, gt=0, description="名字数量")
    model: str = Field("deepseek-v3", description="模型")


class GenerateResponse(BaseModel):
    names: Optional[List[NameView]] = None
    content: Optional[str] = None

