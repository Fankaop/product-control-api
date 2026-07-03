import pytest
from httpx import AsyncClient

BATCH_PAYLOAD = {
    "is_closed": False,
    "task_description": "Test task",
    "work_center_name": "Цех №1",
    "work_center_identifier": "RC-001",
    "shift": "1 смена",
    "team": "Бригада Иванова",
    "batch_number": 11111,
    "batch_date": "2024-01-30",
    "nomenclature": "Болт М10",
    "ekn_code": "EKN-001",
    "shift_start": "2024-01-30T08:00:00",
    "shift_end": "2024-01-30T20:00:00",
}


@pytest.mark.asyncio
async def test_create_batch(auth_client: AsyncClient):
    response = await auth_client.post("/api/v1/batches", json=[BATCH_PAYLOAD])
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 1
    assert data[0]["batch_number"] == 11111


@pytest.mark.asyncio
async def test_get_batch(auth_client: AsyncClient):
    create_resp = await auth_client.post("/api/v1/batches", json=[BATCH_PAYLOAD])
    batch_id = create_resp.json()[0]["id"]

    response = await auth_client.get(f"/api/v1/batches/{batch_id}")
    assert response.status_code == 200
    assert response.json()["id"] == batch_id


@pytest.mark.asyncio
async def test_get_batch_not_found(auth_client: AsyncClient):
    response = await auth_client.get("/api/v1/batches/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_batch_close(auth_client: AsyncClient):
    create_resp = await auth_client.post("/api/v1/batches", json=[BATCH_PAYLOAD])
    batch_id = create_resp.json()[0]["id"]

    response = await auth_client.patch(f"/api/v1/batches/{batch_id}", json={"is_closed": True})
    assert response.status_code == 200
    data = response.json()
    assert data["is_closed"] is True
    assert data["closed_at"] is not None


@pytest.mark.asyncio
async def test_update_batch_reopen(auth_client: AsyncClient):
    create_resp = await auth_client.post("/api/v1/batches", json=[BATCH_PAYLOAD])
    batch_id = create_resp.json()[0]["id"]

    await auth_client.patch(f"/api/v1/batches/{batch_id}", json={"is_closed": True})
    response = await auth_client.patch(f"/api/v1/batches/{batch_id}", json={"is_closed": False})
    assert response.status_code == 200
    assert response.json()["is_closed"] is False
    assert response.json()["closed_at"] is None


@pytest.mark.asyncio
async def test_list_batches(auth_client: AsyncClient):
    await auth_client.post("/api/v1/batches", json=[BATCH_PAYLOAD])
    response = await auth_client.get("/api/v1/batches")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_duplicate_batch(auth_client: AsyncClient):
    await auth_client.post("/api/v1/batches", json=[BATCH_PAYLOAD])
    response = await auth_client.post("/api/v1/batches", json=[BATCH_PAYLOAD])
    assert response.status_code == 409
