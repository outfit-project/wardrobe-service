import io
import os
from uuid import uuid4

os.environ.update(DB_NAME='test', DB_USER='test', DB_PASSWORD='test', SECRET_KEY='test', ML_SERVICE_TOKEN='internal-test-token')

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from PIL import Image
from app.core.security.deps import get_current_user
from app.routers.item import item_router
from app.schemas.item_upload import ClothingItem
from app.schemas.user import UserPayload
from app.services.upload_item import UploadItem
from app.services.update_item import UpdateItem
from app.use_cases.item_case import get_upload_clothing_item_case, get_update_item_case


class Repo:
    def __init__(self): self.items = {}
    async def save(self, item): self.items[item.id] = item
    async def get_by_id(self, item_id): return self.items.get(item_id)
    async def update_processing(self, item_id, **values):
        item = self.items[item_id]
        self.items[item_id] = item.model_copy(update=values)
        return True
    async def claim_retry(self, item_id, user_id):
        item = self.items.get(item_id)
        if not item or item.user_id != user_id or item.processing_status != 'failed': return False
        await self.update_processing(item_id, processing_status='pending', processing_error=None)
        return True


class Storage:
    def __init__(self): self.objects = {}
    async def upload_image(self, file_obj, key, **kwargs): self.objects[key] = file_obj.read()


class Events:
    def __init__(self, fail=False): self.events = []; self.fail = fail
    async def publish(self, event):
        if self.fail: raise ConnectionError('redis down')
        self.events.append(event)


def picture(size=(16,16)):
    data = io.BytesIO(); Image.new('RGB', size, 'red').save(data, format='PNG'); data.seek(0); return data


@pytest.fixture
def api():
    repo, storage, events, owner = Repo(), Storage(), Events(), uuid4()
    upload = UploadItem(repo, storage, events)
    app = FastAPI(); app.include_router(item_router, prefix='/items')
    app.dependency_overrides[get_current_user] = lambda: UserPayload(user_id=owner,username="owner")
    app.dependency_overrides[get_upload_clothing_item_case] = lambda: upload
    app.dependency_overrides[get_update_item_case] = lambda: UpdateItem(repo)
    return TestClient(app), repo, storage, events, owner


def test_image_only_upload_persists_pending_nullable_attributes(api):
    client, repo, storage, events, _ = api
    response = client.post('/items/upload', files={'image': ('shirt.png', picture(), 'image/png')})
    assert response.status_code == 200, response.text
    assert response.json()['processing_status'] == 'pending'
    item = next(iter(repo.items.values()))
    assert item.category is None and item.style is None and item.embedding is None
    assert len(storage.objects) == len(events.events) == 1


@pytest.mark.parametrize('data,mime,status', [(b'not image','image/png',400),(b'x'*(10*1024*1024+1),'image/png',413),(b'png','application/pdf',415)], ids=['corrupt','oversize','mime'])
def test_invalid_upload_rejected_before_writes(api, data, mime, status):
    client, repo, storage, events, _ = api
    response = client.post('/items/upload', files={'image': ('bad.png',data,mime)})
    assert response.status_code == status
    assert not repo.items and not storage.objects and not events.events


def test_too_many_pixels_rejected_before_writes(api):
    client, repo, storage, events, _ = api
    response = client.post('/items/upload', files={'image': ('huge.png',picture((3200,3200)),'image/png')})
    assert response.status_code == 413
    assert not storage.objects


def test_callbacks_require_token_and_complete_atomic_ready_result(api):
    client, repo, _, _, owner = api
    item = ClothingItem(id=uuid4(), user_id=owner, category=None, image_url='test')
    repo.items[item.id] = item
    payload = {'item_id':str(item.id), 'processing_status':'ready', 'embedding':[1.0]*512, 'category':'top', 'subcategory':'t-shirt', 'style':'casual', 'color_hex':'#ff0000'}
    assert client.patch('/items/processing', json=payload).status_code == 401
    headers={'X-Service-Token':'internal-test-token'}
    invalid = dict(payload); invalid.pop('style')
    assert client.patch('/items/processing', json=invalid, headers=headers).status_code == 422
    assert repo.items[item.id].embedding is None
    assert client.patch('/items/processing', json=payload, headers=headers).status_code == 200
    assert repo.items[item.id].processing_status == 'ready' and repo.items[item.id].subcategory == 't-shirt'
    assert client.patch('/items/embedding', json={'item_id':str(item.id),'embedding':[0.5]*512},headers=headers).status_code == 200
    assert repo.items[item.id].category == 'top'


@pytest.mark.asyncio
async def test_queue_failure_is_visible_failed_not_permanent_pending():
    repo, storage, events, owner = Repo(), Storage(), Events(fail=True), uuid4()
    response = await UploadItem(repo,storage,events).execute(user_id=owner,file_obj=picture(),filename='a.png',content_type='image/png')
    assert response['processing_status'] == 'failed'
    assert next(iter(repo.items.values())).processing_error


@pytest.mark.asyncio
async def test_only_owner_can_retry_failed_item():
    repo, storage, events, owner = Repo(), Storage(), Events(), uuid4()
    service = UploadItem(repo,storage,events)
    item = ClothingItem(id=uuid4(), user_id=owner, image_url='key',processing_status='failed',processing_error='bad photo')
    repo.items[item.id]=item
    with pytest.raises(HTTPException) as error: await service.retry(item_id=item.id,user_id=uuid4())
    assert error.value.status_code == 404
    result=await service.retry(item_id=item.id,user_id=owner)
    assert result['processing_status']=='pending' and repo.items[item.id].processing_error is None
    with pytest.raises(HTTPException) as error: await service.retry(item_id=item.id,user_id=owner)
    assert error.value.status_code==409
    assert len(events.events)==1


def test_retry_route_hides_foreign_and_rejects_nonfailed(api):
    client, repo, _, events, owner = api
    item=ClothingItem(id=uuid4(),user_id=owner,image_url='key',processing_status='failed')
    repo.items[item.id]=item
    response=client.post(f'/items/{item.id}/retry')
    assert response.status_code==200 and response.json()['processing_status']=='pending'
    assert client.post(f'/items/{item.id}/retry').status_code==409
    item2=item.model_copy(update={'id':uuid4(),'user_id':uuid4(),'processing_status':'failed'})
    repo.items[item2.id]=item2
    assert client.post(f'/items/{item2.id}/retry').status_code==404
    assert len(events.events)==1


def test_invalid_inference_values_rejected_without_mutation(api):
    client,repo,_,_,owner=api
    item=ClothingItem(id=uuid4(),user_id=owner,image_url='key')
    repo.items[item.id]=item
    headers={'X-Service-Token':'internal-test-token'}
    base={'item_id':str(item.id),'processing_status':'ready','category':'top','subcategory':'t-shirt','style':'casual','color_hex':'#ff0000','embedding':[1.0]*512}
    for change in ({'embedding':[1.0]*5},{'color_hex':'#gggggg'},{'category':None},{'embedding':[0.0]*512}):
        assert client.patch('/items/processing',json=base|change,headers=headers).status_code==422
    assert repo.items[item.id].processing_status=='pending'


@pytest.mark.parametrize('route', ['processing', 'embedding'])
@pytest.mark.parametrize('token', ['', 'wrong-token'])
def test_both_callbacks_reject_invalid_service_tokens_without_mutation(api, route, token):
    client, repo, _, _, owner = api
    item = ClothingItem(id=uuid4(), user_id=owner, image_url='key')
    repo.items[item.id] = item
    payload = {'item_id': str(item.id), 'embedding': [1.0] * 512}
    if route == 'processing':
        payload['processing_status'] = 'processing'
    response = client.patch(f'/items/{route}', json=payload, headers={'X-Service-Token': token})
    assert response.status_code == 401
    assert repo.items[item.id].processing_status == 'pending'
    assert repo.items[item.id].embedding is None
