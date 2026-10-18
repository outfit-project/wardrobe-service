import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ItemORM(Base):
    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), index=True)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    image_url: Mapped[str] = mapped_column(String(1024))
    subcategory: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    style: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    color_hex: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    embedding: Mapped[Optional[list[float]]] = mapped_column(JSONB, nullable=True)
    processing_status: Mapped[str] = mapped_column(String(16), default="pending", server_default="pending")
    processing_error: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )