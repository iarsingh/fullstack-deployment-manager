# Full-stack deployment manager

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
