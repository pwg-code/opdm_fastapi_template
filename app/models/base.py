from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import func

def utcnow() -> datetime:
    return datetime.now()


class DatabaseModel(SQLModel):
    """所有数据库模型的基类"""

    id: int | None = Field(default=None, primary_key=True, sa_column_kwargs={"autoincrement": True, "comment": "主键"})
    created_at: datetime = Field(default_factory=utcnow, nullable=False, sa_column_kwargs={"comment": "创建时间"})
    updated_at: datetime = Field(default_factory=utcnow, nullable=False, sa_column_kwargs={"onupdate": utcnow, "comment": "更新时间"})
    created_by: str | None = Field(default=None, max_length=64, sa_column_kwargs={"comment": "创建人"})
    updated_by: str | None = Field(default=None, max_length=64, sa_column_kwargs={"comment": "更新人"})

