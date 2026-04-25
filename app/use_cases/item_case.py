from typing import Annotated

from fastapi import Depends

from app.core.config import settings
from app.db.redis import RedisDep
from app.db.session import SessionDep
from app.messaging.redis_publisher import RedisPublisher
from app.repositories.item import ClothingRepository
from app.repositories.storage import ImageStorage
from app.services import ClothingItemImage, GetUserWardrobe, UploadItem


def get_clothing_item_image_case(session: SessionDep) -> ClothingItemImage:
    return ClothingItemImage(
        ClothingRepository(session),
        ImageStorage(settings),
    )


def get_user_wardrobe_case(session: SessionDep) -> GetUserWardrobe:
    return GetUserWardrobe(repo=ClothingRepository(session))


def get_upload_clothing_item_case(
    session: SessionDep,
    redis: RedisDep,
) -> UploadItem:
    return UploadItem(
        ClothingRepository(session),
        ImageStorage(settings),
        RedisPublisher(redis, queue_name=settings.ML_TASKS_QUEUE),
    )


UploadClothingItemDep = Annotated[
    UploadItem,
    Depends(get_upload_clothing_item_case),
]

GetClothingItemImageDep = Annotated[
    ClothingItemImage,
    Depends(get_clothing_item_image_case),
]

GetUserWardrobeDep = Annotated[
    GetUserWardrobe,
    Depends(get_user_wardrobe_case),
]
