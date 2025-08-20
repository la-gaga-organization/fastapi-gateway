from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import DateTime, Integer, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="sessions")  # noqa: F821
    refreshTokens: Mapped[List["RefreshToken"]] = relationship("RefreshToken", back_populates="session")  # noqa: F821
    accessTokens: Mapped[List["AccessToken"]] = relationship("AccessToken", back_populates="session")  # noqa: F821
