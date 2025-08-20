from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, DateTime, Integer, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RefreshToken(Base):
    __tablename__ = "refreshTokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    token: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    accessToken_id: Mapped[int] = mapped_column(ForeignKey("accessTokens.id"))
    is_expired: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    session: Mapped["Session"] = relationship("Session", back_populates="refreshTokens")  # noqa: F821
    accessToken: Mapped["AccessToken"] = relationship("AccessToken", back_populates="refreshToken")  # noqa: F821
