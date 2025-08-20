from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import String, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(80), index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    password: Mapped[str] = mapped_column(String(80), index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    tokens: Mapped[List["Token"]] = relationship("Token", back_populates="user")  # noqa: F821
