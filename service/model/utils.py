# -*- coding:utf-8 -*-
# ====================
# Author liuyuchen
# Date 2025/2/15
# 
# ====================
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, text
from sqlmodel import SQLModel, Field



class TimestampMixin(SQLModel):
    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: datetime2timestamp(v),
        }

    created_at: Optional[datetime] = Field(
        sa_type=DateTime, default=None, nullable=False,  sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )
    updated_at: Optional[datetime] = Field(
        sa_type=DateTime, default=None, sa_column_kwargs={"onupdate": text("CURRENT_TIMESTAMP")}
    )


def datetime2timestamp(value: datetime):
    if not value:
        return None
    return value.timestamp()

