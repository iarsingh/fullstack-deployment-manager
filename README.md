# Full-stack deployment manager

<!-- project-guide:start -->
## Project guide

[Project architecture](PROJECT_ARCHITECTURE.md) · [Interview questions and answers](INTERVIEW_QA.md)

Use the architecture document for the component diagram, implementation boundaries, and verification entry points. The interview guide includes source-backed answers and project walkthroughs.

### Implementation map

| Component | Responsibility |
| --- | --- |
| [`src/deploys/main.py`](src/deploys/main.py) | HTTP handlers: `GET /healthz`, `GET /deployments`, `POST /deployments`, `GET /deployments/{deployment_id}`, `POST /deployments/{deployment_id}/status` |
| [`src/deploys/ops.py`](src/deploys/ops.py) | HTTP handlers: `GET /readyz`, `POST /workspaces`, `GET /workspaces`, `POST /workspaces/{workspace_id}/jobs`, `GET /jobs/{job_id}` |
| [`src/deploys/store.py`](src/deploys/store.py) | Functions: `now`, `__init__`, `__init__`, `clear`, `validate`, `create`, `get` |
| [`web/package.json`](web/package.json) | User interface code/assets |
| [`requirements.txt`](requirements.txt) | Implementation or supporting configuration |
| [`web/src/App.tsx`](web/src/App.tsx) | User interface code/assets |
| [`Dockerfile`](Dockerfile) | Container build/service configuration |
| [`Makefile`](Makefile) | Implementation or supporting configuration |
| [`docker-compose.yml`](docker-compose.yml) | Container build/service configuration |
| [`tests/test_deploys.py`](tests/test_deploys.py) | Executable checks and regression examples |
| [`tests/test_ops.py`](tests/test_ops.py) | Executable checks and regression examples |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | GitHub Actions job definitions |
| [`README.md`](README.md) | Project explanations or operating notes |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Project explanations or operating notes |

### Local setup and verification

From the repository root (the commands follow the checked-in manifests):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

To serve the FastAPI application locally, install the server separately if it is not already available:

```bash
python -m pip install uvicorn
PYTHONPATH=src python -m uvicorn deploys.main:app --reload
```

<!-- project-guide:end -->

Level: Intermediate

Skills: React, TypeScript, FastAPI, Docker, state machines

The API records a deployment of a pinned image to `dev` or `staging` and walks it through a lifecycle. The React page in `web/src/App.tsx` creates deployments, moves them along, and offers a rollback when one fails.

```text
pending -> running -> succeeded
        \          \-> failed -> rollback creates a new pending deployment of the last good image
         \-> cancelled
```

```bash
pip install -r requirements.txt
pytest -q
docker compose up --build
```

| Method and path | Does |
| --- | --- |
| `POST /deployments` | Record `name`, `environment`, `image`. Returns 201 and `pending` |
| `GET /deployments?environment=staging&name=billing` | List, filtered |
| `GET /deployments/{id}` | One deployment with its history |
| `POST /deployments/{id}/status` | Move to `running`, `succeeded`, `failed`, or `cancelled` |
| `POST /deployments/{id}/rollback` | Redeploy the last succeeded image for that service and environment |

## What it refuses

- `prod`. Production is recorded by a pull request, not this form.
- An image without a tag, or tagged `latest`.
- A second deployment of the same service to the same environment while one is pending or running (409).
- A move the lifecycle does not allow, such as pending straight to succeeded (409).
- A rollback when there is no earlier successful deployment (409).

The store is in memory, so a restart clears it. It records deployments; it does not run them.

## Ops plane

Workspaces, tenant isolation, job approval, and audit live under `/v1`. Production apply is refused. See `docs/ARCHITECTURE.md`.
