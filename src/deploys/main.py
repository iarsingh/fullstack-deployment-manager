from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Deployment manager")
ROWS = []


class Deployment(BaseModel):
    name: str
    environment: str


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/deployments")
def list_deployments():
    return {"deployments": ROWS}


@app.post("/deployments")
def create_deployment(body: Deployment):
    if body.environment == "prod":
        raise HTTPException(status_code=422, detail="prod is recorded by a pull request, not this form")
    if body.environment not in {"dev", "staging"}:
        raise HTTPException(status_code=422, detail="environment must be dev or staging")
    row = {"id": f"dep-{len(ROWS) + 1}", "name": body.name, "environment": body.environment}
    ROWS.append(row)
    return row
