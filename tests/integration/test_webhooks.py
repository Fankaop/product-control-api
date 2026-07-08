import pytest
from httpx import AsyncClient


WEBHOOK_PAYLOAD = {
    "url": "https://example.com/hook",
    "events": ["batch_created", "batch_closed"],
    "secret_key": "supersecret",
    "retry_count": 5,
    "timeout": 15,
}


@pytest.mark.asyncio
async def test_create_webhook(auth_client: AsyncClient):
    response = await auth_client.post("/api/v1/webhooks", json=WEBHOOK_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["url"] == WEBHOOK_PAYLOAD["url"]
    assert data["events"] == WEBHOOK_PAYLOAD["events"]
    assert data["retry_count"] == 5
    assert data["timeout"] == 15
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_list_webhooks(auth_client: AsyncClient):
    await auth_client.post("/api/v1/webhooks", json=WEBHOOK_PAYLOAD)
    response = await auth_client.get("/api/v1/webhooks")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_update_webhook(auth_client: AsyncClient):
    create_resp = await auth_client.post("/api/v1/webhooks", json=WEBHOOK_PAYLOAD)
    webhook_id = create_resp.json()["id"]

    response = await auth_client.patch(f"/api/v1/webhooks/{webhook_id}", json={"is_active": False})
    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_delete_webhook(auth_client: AsyncClient):
    create_resp = await auth_client.post("/api/v1/webhooks", json=WEBHOOK_PAYLOAD)
    webhook_id = create_resp.json()["id"]

    response = await auth_client.delete(f"/api/v1/webhooks/{webhook_id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_deliveries_empty(auth_client: AsyncClient):
    create_resp = await auth_client.post("/api/v1/webhooks", json=WEBHOOK_PAYLOAD)
    webhook_id = create_resp.json()["id"]

    response = await auth_client.get(f"/api/v1/webhooks/{webhook_id}/deliveries")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_webhook_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/webhooks")
    assert response.status_code == 401
