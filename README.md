# Full-stack deployment manager

Level: Intermediate

Skills: React, TypeScript, FastAPI, Docker

The API records a deployment name and an environment. `prod` is refused. The React page in `web/src/App.tsx` reads `GET /deployments`.

Docker Compose runs the API. The page is the front end you wire to that API. This store is in memory, so a restart clears it. It does not deploy anything.

```bash
pip install -r requirements.txt
pytest -q
docker compose up --build
```

