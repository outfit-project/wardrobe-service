from botocore.exceptions import ClientError
from app.core.config import Settings
from app.storage.minio_session import session_minio


async def unsure_bucket(settings: Settings):
    if not settings.MINIO_ENDPOINT or not settings.MINIO_BUCKET:
        raise Exception("MINIO_ENDPOINT and MINIO_BUCKET must be set")
    async with session_minio.client(
            "s3",
            endpoint_url=settings.MINIO_ENDPOINT,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,

    ) as s3:
        try:
            await s3.head_bucket(Bucket=settings.MINIO_BUCKET)
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchBucket"):
                await s3.create_bucket(Bucket=settings.MINIO_BUCKET)
            else:
                raise
