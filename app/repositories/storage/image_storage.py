from app.core.config import Settings
from app.repositories.storage.minio_session import session_minio


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
        extra: dict[str, str] = {}
        if content_type:
            extra["ContentType"] = content_type
        async with session_minio.client(
                "s3",
                endpoint_url=self._settings.MINIO_ENDPOINT,
                aws_access_key_id=self._settings.MINIO_ACCESS_KEY,
                aws_secret_access_key=self._settings.MINIO_SECRET_KEY,
        ) as s3:
            bucket = self._settings.MINIO_BUCKET
            if extra:
                await s3.upload_fileobj(file_obj, bucket, key, ExtraArgs=extra)
            else:
                await s3.upload_fileobj(file_obj, bucket, key)

    async def get_bytes(self, key: str) -> tuple[bytes, str]:
        async with session_minio.client(
                "s3",
                endpoint_url=self._settings.MINIO_ENDPOINT,
                aws_access_key_id=self._settings.MINIO_ACCESS_KEY,
                aws_secret_access_key=self._settings.MINIO_SECRET_KEY,
        ) as s3:
            response = await s3.get_object(
                Bucket=self._settings.MINIO_BUCKET,
                Key=key,
            )
            data = await response["Body"].read()
            content_type = response.get("ContentType", "image/jpeg")

            return data, content_type
