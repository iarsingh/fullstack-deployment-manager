from fastapi.testclient import TestClient

from deploys.main import ROWS, app

client = TestClient(app)


def test_prod_is_refused_and_dev_is_listed():
    ROWS.clear()
    assert client.post("/deployments", json={"name": "billing", "environment": "prod"}).status_code == 422
    created = client.post("/deployments", json={"name": "billing", "environment": "dev"}).json()
    assert created["id"] == "dep-1"
    assert client.get("/deployments").json()["deployments"][0]["name"] == "billing"
