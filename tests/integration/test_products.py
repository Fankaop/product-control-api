import pytest
from httpx import AsyncClient

BATCH_PAYLOAD = {
    "is_closed": False,
    "task_description": "Test task",
    "work_center_name": "Цех №1",
    "work_center_identifier": "RC-002",
    "shift": "1 смена",
    "team": "Бригада Петрова",
    "batch_number": 22222,
    "batch_date": "2024-02-15",
    "nomenclature": "Гайка М10",
    "ekn_code": "EKN-002",
    "shift_start": "2024-02-15T08:00:00",
    "shift_end": "2024-02-15T20:00:00",
}


@pytest.mark.asyncio
async def test_add_product(auth_client: AsyncClient):
    batch_resp = await auth_client.post("/api/v1/batches", json=[BATCH_PAYLOAD])
    batch_id = batch_resp.json()[0]["id"]

    response = await auth_client.post("/api/v1/products", json={
        "unique_code": "CODE-001",
        "batch_id": batch_id,
    })
    assert response.status_code == 201
    assert response.json()["unique_code"] == "CODE-001"
    assert response.json()["is_aggregated"] is False


@pytest.mark.asyncio
async def test_aggregate_product(auth_client: AsyncClient):
    batch_resp = await auth_client.post("/api/v1/batches", json=[BATCH_PAYLOAD])
    batch_id = batch_resp.json()[0]["id"]

    await auth_client.post("/api/v1/products", json={
        "unique_code": "CODE-AGG-001",
        "batch_id": batch_id,
    })

    response = await auth_client.post(
        f"/api/v1/batches/{batch_id}/aggregate",
        json={"unique_code": "CODE-AGG-001"},
    )
    assert response.status_code == 200
    assert response.json()["is_aggregated"] is True
    assert response.json()["aggregated_at"] is not None


@pytest.mark.asyncio
async def test_aggregate_already_aggregated(auth_client: AsyncClient):
    batch_resp = await auth_client.post("/api/v1/batches", json=[BATCH_PAYLOAD])
    batch_id = batch_resp.json()[0]["id"]

    await auth_client.post("/api/v1/products", json={
        "unique_code": "CODE-DOUBLE",
        "batch_id": batch_id,
    })
    await auth_client.post(
        f"/api/v1/batches/{batch_id}/aggregate",
        json={"unique_code": "CODE-DOUBLE"},
    )
    response = await auth_client.post(
        f"/api/v1/batches/{batch_id}/aggregate",
        json={"unique_code": "CODE-DOUBLE"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_aggregate_product_not_found(auth_client: AsyncClient):
    batch_resp = await auth_client.post("/api/v1/batches", json=[BATCH_PAYLOAD])
    batch_id = batch_resp.json()[0]["id"]

    response = await auth_client.post(
        f"/api/v1/batches/{batch_id}/aggregate",
        json={"unique_code": "NONEXISTENT"},
    )
    assert response.status_code == 404
