from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import func


class DatabaseModel(SQLModel):
    """所有数据库模型的基类"""

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = Field(
        default_factory=datetime.now,
        sa_column_kwargs={
            "server_default": func.now(),
            "nullable": False,
        },
    )
