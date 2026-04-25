from typing import Annotated

from fastapi import Request, Depends
from redis.asyncio import Redis

from app.core.config import settings
from app.db.session import SessionDep
from app.messaging.redis_publisher import RedisPublisher
from app.repositories.item import ClothingRepository
from app.repositories.storage import ImageStorage
from app.services import UploadItem


def get_redis(request: Request) -> Redis:
    return request.app.state.redis


def get_upload_clothing_item_case(
        session: SessionDep,
        redis: Annotated[Redis, Depends(get_redis)],
) -> UploadItem:
    return UploadItem(
        ClothingRepository(session),
        ImageStorage(settings),
        RedisPublisher(Redis, queue_name=settings.ML_),
    )