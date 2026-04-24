import uuid
from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ItemORM(Base):
    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), index=True)
    category: Mapped[str] = mapped_column(String(64))
    image_url: Mapped[str] = mapped_column(String(1024))
    subcategory: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    style: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    color_hex: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    embedding: Mapped[Optional[list[float]]] = mapped_column(Vector(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )