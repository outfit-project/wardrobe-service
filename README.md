# Wardrobe service

Owns garment records, photo storage, owner access and the asynchronous processing lifecycle. Built with FastAPI, PostgreSQL, Redis and S3-compatible object storage.

[Project overview](../../README.md) · [ML worker](../ml-inference/README.md) · [Outfit service](../outfit-service/README.md)

## Upload lifecycle

1. The user uploads a single photo; category/style fields are optional.
2. The API validates the image, stores it in S3, creates a `pending` item and queues inference in Redis.
3. The ML worker reports `processing`, then atomically saves complete metadata and the embedding with `ready`, or reports `failed`.
4. The owner can retry a failed item. Pending/processing items are excluded from outfit suggestions.

Images must be JPEG, PNG or WebP, at most **10 MiB** and **10 million pixels**. MIME type and actual decoded content are checked before storage/database writes. The worker determines metadata even when legacy form fields were supplied.

Records store UUIDs, owner ID, storage key, category, subcategory, style, color hex, embedding, processing status/error and creation time. Metadata is nullable before inference. Embeddings are stored as JSONB; historical migrations still require the pgvector-capable PostgreSQL image. The lifecycle migration marks legacy records with both an embedding and category ready; other legacy records become failed so they can be retried.

## HTTP API

Public base URL: `http://localhost:8080`. Owner endpoints require `Authorization: Bearer <access_token>`.

| Method | Path | Authentication | Result |
| --- | --- | --- | --- |
| GET | `/items/` | Owner JWT | `{items: [...], total}` |
| POST | `/items/upload` | Owner JWT | `{item_id, image_url, processing_status}` |
| GET | `/items/{item_id}/image` | Public UUID URL | Image bytes; cache lifetime 86400 seconds |
| DELETE | `/items/{item_id}` | Owner JWT | 204; 404 if absent/not owned |
| POST | `/items/{item_id}/retry` | Owner JWT | Requeued upload-shaped response |
| PATCH | `/items/processing` | `X-Service-Token` | Internal processing callback; 200 |
| PATCH | `/items/embedding` | `X-Service-Token` | Legacy embedding callback; 200 |

The upload request is multipart with an `image` field. Optional legacy fields are `category`, `subcategory`, `style` and `color_hex`. Example for a Bash-compatible shell, with an access token already set:

```bash
curl -X POST http://localhost:8080/items/upload \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "image=@/path/to/shirt.jpg"
```

List responses expose `id`, `user_id`, `image_url`, nullable metadata/embedding, `processing_status`, `processing_error` and `created_at`. Returned image URLs use `PUBLIC_BASE_URL`, not the internal S3 endpoint.

Photo URLs are public bearer links identified by UUID: anyone with the URL can view the photo. Listing, deleting and retrying require ownership. Deletion removes the item record; it does not currently remove the underlying S3 object. Photos and records are not saved in a distributed transaction.

Retry returns 404 for another owner's item and 409 unless the state is `failed`. The state claim is atomic. A queue-publication failure leaves the saved item `failed` with a retryable explanation. Image errors use 400 (decode), 413 (size/pixels) or 415 (format); invalid request schemas use 422.

## Internal contracts

The Redis `ml_tasks` list receives JSON text via `RPUSH`:

```json
{
  "event_type": "new_item_uploaded",
  "data": {
    "item_id": "00000000-0000-4000-8000-000000000001",
    "user_id": "00000000-0000-4000-8000-000000000002",
    "image_url": "users/<user_id>/items/<item_id>.jpg"
  }
}
```

Here `image_url` is an **object key**, not a public URL. The callback body always includes `item_id` and `processing_status` (`processing`, `ready` or `failed`). A `ready` callback also requires `category`, `subcategory`, `style`, `color_hex` and a finite nonzero embedding of exactly `EMBEDDING_DIM` values. Metadata and state are saved together. Invalid service tokens return 401, missing items 404, invalid callback data 422.

The legacy embedding callback accepts `item_id`, `embedding`, optional `category`/`style` and does not advance the processing lifecycle; new workers should use `/items/processing`.

## Configuration

Settings: [app/core/config.py](app/core/config.py). The following values describe root Compose:

| Variable | Value / purpose |
| --- | --- |
| `DB_HOST`, `DB_PORT`, `DB_NAME` | `wardrobe-db`, `5432`, `wardrobe_db` |
| `DB_USER`, `DB_PASSWORD` | Root configuration |
| `REDIS_URL`, `ML_TASKS_QUEUE` | `redis://wardrobe-redis:6379/0`, `ml_tasks` |
| `SECRET_KEY`, `ALGORITHM` | Shared auth JWT secret; `HS256` |
| `ML_SERVICE_TOKEN` | Generated callback secret; must match ML |
| `EMBEDDING_DIM` | `512`; must match the model |
| `MINIO_ENDPOINT` | `http://minio:9000` |
| `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET` | Shared S3 credentials/bucket; default bucket `wardrobe-photos` |
| `PUBLIC_BASE_URL` | `http://localhost:8080`; browser-reachable gateway URL |
| `CORS_ORIGINS`, `DEBUG` | Root browser origins; `false` |

The service reads its local `.env`; root Compose injects its own explicit environment. Add application-only overrides to Compose rather than assuming every root `.env` key is forwarded.

## Run, health and checks

From the project root:

```bash
python scripts/setup.py
docker compose up --build -d --wait --wait-timeout 900
docker compose logs -f wardrobe ml-inference
curl http://localhost:8080/health/wardrobe
```

The container applies Alembic migrations before Uvicorn on port 8000. Lifespan startup creates the S3 bucket if missing. `/health/live` checks the process; `/health/ready` checks PostgreSQL and Redis. Readiness does not continuously probe S3 or the ML worker.

For native development, configure reachable database/Redis/S3 endpoints, run `alembic upgrade head`, then `uvicorn app.main:app --reload --port 8000` here. Internal Compose dependencies have no published host ports.

In an isolated Python 3.12 environment, from the project root:

```bash
python -m pip install -r backend/wardrobe-service/requirements.txt -r requirements-test.txt
cd backend/wardrobe-service
python -m pytest -q
python -m compileall -q app
```

Tests cover photo-only uploads, validation, failed enqueue/retry and protected processing callbacks. The root smoke script exercises real photo inference; see [verification](../../docs/verification.md).
