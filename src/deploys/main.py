from deploys.ops import router as ops_router
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from deploys.store import DeployError, Store

app = FastAPI(title="Deployment manager")
app.include_router(ops_router, prefix="/v1")
STORE = Store()
ROWS = STORE.rows


class Deployment(BaseModel):
    name: str
    environment: str
    image: str


class Transition(BaseModel):
    status: Literal["running", "succeeded", "failed", "cancelled"]


def guarded(action):
    try:
        return action()
    except DeployError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc)) from exc


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/deployments")
def list_deployments(environment: str | None = None, name: str | None = None):
    return {"deployments": STORE.list(environment, name)}


@app.post("/deployments", status_code=201)
def create_deployment(body: Deployment):
    return guarded(lambda: STORE.create(body.name, body.environment, body.image))


@app.get("/deployments/{deployment_id}")
def get_deployment(deployment_id: str):
    return guarded(lambda: STORE.get(deployment_id))


@app.post("/deployments/{deployment_id}/status")
def move_deployment(deployment_id: str, body: Transition):
    return guarded(lambda: STORE.transition(deployment_id, body.status))


@app.post("/deployments/{deployment_id}/rollback", status_code=201)
def rollback_deployment(deployment_id: str):
    return guarded(lambda: STORE.rollback(deployment_id))
