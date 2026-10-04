import pytest
from fastapi.testclient import TestClient

from deploys.main import STORE, app

client = TestClient(app)


@pytest.fixture(autouse=True)
def empty_store():
    STORE.clear()


def deploy(name="billing", environment="dev", image="billing:1.4.2"):
    return client.post("/deployments", json={"name": name, "environment": environment, "image": image})


def move(deployment_id, status):
    return client.post(f"/deployments/{deployment_id}/status", json={"status": status})


def test_prod_is_refused_and_dev_is_listed():
    assert deploy(environment="prod").status_code == 422
    created = deploy().json()
    assert created["id"] == "dep-1"
    assert created["status"] == "pending"
    assert client.get("/deployments").json()["deployments"][0]["name"] == "billing"


def test_latest_and_untagged_images_are_refused():
    assert "latest is refused" in deploy(image="billing:latest").json()["detail"]
    assert deploy(image="billing").status_code == 422


def test_bad_name_is_refused():
    assert deploy(name="Billing Service").status_code == 422


def test_lifecycle_records_each_step():
    created = deploy().json()
    move(created["id"], "running")
    done = move(created["id"], "succeeded").json()
    assert [step["status"] for step in done["history"]] == ["pending", "running", "succeeded"]


def test_illegal_transition_is_409():
    created = deploy().json()
    response = move(created["id"], "succeeded")
    assert response.status_code == 409
    assert "from pending to succeeded" in response.json()["detail"]


def test_second_deploy_while_one_is_in_progress_is_409():
    deploy()
    assert deploy(image="billing:1.4.3").status_code == 409
    assert deploy(environment="staging").status_code == 201


def test_rollback_redeploys_the_last_good_image():
    first = deploy(image="billing:1.4.2").json()
    move(first["id"], "running")
    move(first["id"], "succeeded")
    second = deploy(image="billing:1.5.0").json()
    move(second["id"], "running")
    move(second["id"], "failed")
    rollback = client.post(f"/deployments/{second['id']}/rollback")
    assert rollback.status_code == 201
    assert rollback.json()["image"] == "billing:1.4.2"
    assert rollback.json()["rollback_of"] == second["id"]


def test_rollback_without_a_good_deploy_is_409():
    first = deploy().json()
    move(first["id"], "running")
    move(first["id"], "failed")
    assert client.post(f"/deployments/{first['id']}/rollback").status_code == 409


def test_filter_and_missing_id():
    deploy(name="billing")
    deploy(name="search", environment="staging", image="search:2.0.0")
    assert len(client.get("/deployments", params={"environment": "staging"}).json()["deployments"]) == 1
    assert client.get("/deployments/dep-99").status_code == 404
