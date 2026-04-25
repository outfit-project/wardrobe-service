from typing import Annotated

from fastapi import Depends

from app.core.config import settings
from app.db.session import SessionDep
from app.repositories.item import ClothingRepository
from app.repositories.storage import ImageStorage
from app.services import ClothingItemImage, UploadItem


def get_clothing_item_image_case(session: SessionDep) -> ClothingItemImage:
    return ClothingItemImage(
        ClothingRepository(session),
        ImageStorage(settings)
    )

UploadClothingItemDep = Annotated[
    UploadItem,
    Depends(get_clothing_item_image_case)
]


GetClothingItemImageDep = Annotated[
    ClothingItemImage,
    Depends(get_clothing_item_image_case),
]
