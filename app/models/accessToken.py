from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, DateTime, Integer, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AccessToken(Base):
    __tablename__ = "accessTokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    token: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    is_expired: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    session: Mapped["Session"] = relationship("Session", back_populates="accessTokens")  # noqa: F821
    refreshToken: Mapped["RefreshToken"] = relationship("RefreshToken", back_populates="accessToken")  # noqa: F821
