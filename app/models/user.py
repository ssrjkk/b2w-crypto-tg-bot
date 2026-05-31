"""User model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    id: int
    telegram_id: int = Field(unique=True)
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
