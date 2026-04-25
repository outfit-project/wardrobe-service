import json

from redis.asyncio import Redis

from app.schemas.item_upload import ItemUploadedEvent


class RedisPublisher:
    def __init__(
            self,
            redis_client: Redis,
            queue_name: str,
    ) -> None:
        self._redis = redis_client
        self._queue = queue_name

    async def publish(self, event: ItemUploadedEvent) -> None:
        payload = {
            "event_type": "new_item_uploaded",
            "data": {
                "item_id": str(event.item_id),
                "user_id": str(event.user_id),
                "image_url": event.image_url,
            }
        }
        await self._redis.rpush(self._queue, json.dumps(payload))
