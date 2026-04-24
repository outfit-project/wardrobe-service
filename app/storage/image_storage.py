from app.core.config import Settings, settings
from app.storage.minio_session import session_minio


class ImageStorage:
    def __init__(self, settings: Settings):
        self._settings = settings

    async def upload_image(
            self,
            file_obj,
            key: str,
            *,
            content_type: str | None = None,
    ):
        extra: dict = {}
        if content_type:
            extra["content_type"] = content_type
        async with session_minio.client(
                "s3",
                endpoint_url=settings.MINIO_ENDPOINT,
                aws_access_key_id=settings.MINIO_ACCESS_KEY,
                aws_secret_access_key=settings.MINIO_SECRET_KEY,
        ) as s3:
            bucket = self._settings.MINIO_BUCKET
            if extra:
                await s3.upload_object(file_obj, bucket, key, ExtraArgs=extra)
            else:
                await s3.upload_object(file_obj, bucket, key)

    async def get_bytes(self, key: str) -> tuple[bytes, str]:
        async with session_minio.client(
                "s3",
                endpoint_url=settings.MINIO_ENDPOINT,
                aws_access_key_id=settings.MINIO_ACCESS_KEY,
                aws_secret_access_key=settings.MINIO_SECRET_KEY,
        ) as s3:
            response = await s3.get_object(
                Bucket=settings.MINIO_BUCKET,
                Key=key,
            )
            data = await response["Body"].read()
            content_type = response["ContentType", "image/jpeg"]

            return data, content_type
