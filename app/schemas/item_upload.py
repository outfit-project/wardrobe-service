import uuid
from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field, FiniteFloat, model_validator
from app.schemas.categories import Category, Style

ProcessingStatus = Literal['pending', 'processing', 'ready', 'failed']


class ItemUploadedEvent(BaseModel):
    event_type: str = 'item.uploaded'
    item_id: uuid.UUID
    user_id: uuid.UUID
    image_url: str


class ClothingItem(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    category: Category | None = None
    image_url: str
    subcategory: str | None = None
    style: Style | None = None
    color_hex: str | None = None
    embedding: list[float] | None = None
    processing_status: ProcessingStatus = 'pending'
    processing_error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WardrobeResponse(BaseModel):
    items: list[ClothingItem]
    total: int


class UploadClothingItemResponse(BaseModel):
    item_id: str
    image_url: str
    processing_status: ProcessingStatus = 'pending'


class UpdateEmbeddingRequest(BaseModel):
    item_id: uuid.UUID
    embedding: list[FiniteFloat] = Field(min_length=1, max_length=4096)
    style: Style | None = None
    category: Category | None = None


class UpdateProcessingRequest(BaseModel):
    item_id: uuid.UUID
    processing_status: Literal['processing', 'ready', 'failed']
    embedding: list[FiniteFloat] | None = Field(default=None, min_length=1, max_length=4096)
    category: Category | None = None
    subcategory: str | None = Field(default=None, min_length=1, max_length=128)
    style: Style | None = None
    color_hex: str | None = Field(default=None, pattern=r'^#[0-9a-fA-F]{6}$')
    processing_error: str | None = Field(default=None, max_length=500)

    @model_validator(mode='after')
    def complete_ready_result(self):
        if self.processing_status == 'ready':
            if any(value is None for value in (self.embedding,self.category,self.subcategory,self.style,self.color_hex)):
                raise ValueError('Ready requires complete inference metadata')
            if not any(self.embedding):
                raise ValueError('Embedding must be nonzero')
        return self
