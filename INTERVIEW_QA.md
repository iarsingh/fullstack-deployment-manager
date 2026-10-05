# fullstack-deployment-manager — interview questions and answers

[README](README.md) · [Project architecture](PROJECT_ARCHITECTURE.md)

Answers below use this repository’s files and implementation. They distinguish existing behavior from suggested extensions; source links let you verify each walkthrough.

## 1. What problem does fullstack-deployment-manager address, and what can you demonstrate?

The API records a deployment of a pinned image to `dev` or `staging` and walks it through a lifecycle. The React page in `web/src/App.tsx` creates deployments, moves them along, and offers a rollback when one fails.

I would demonstrate the linked implementation or examples and distinguish that evidence from any planned production features. Start with [`README.md`](README.md).

## 2. How is this repository organized?

- [`src/deploys/main.py`](src/deploys/main.py): Implementation or supporting configuration.
- [`src/deploys/store.py`](src/deploys/store.py): Implementation or supporting configuration.
- [`web/package.json`](web/package.json): User interface code/assets.
- [`requirements.txt`](requirements.txt): Implementation or supporting configuration.
- [`web/src/App.tsx`](web/src/App.tsx): User interface code/assets.
- [`Dockerfile`](Dockerfile): Container build/service configuration.
- [`docker-compose.yml`](docker-compose.yml): Container build/service configuration.
- [`tests/test_deploys.py`](tests/test_deploys.py): Executable checks and regression examples.

[PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) contains the component diagram and the implementation walkthrough.

## 3. Can you walk through `create` and explain the decision it makes?

The main walkthrough here is `create(self, name, environment, image, rollback_of=None)` in [`src/deploys/store.py`](src/deploys/store.py#L44).

```python
    def create(self, name, environment, image, rollback_of=None):
        self.validate(name, environment, image)
        active = [row for row in self.rows if row["name"] == name and row["environment"] == environment and row["status"] in {"pending", "running"}]
        if active:
            raise DeployError(f"{name} already has {active[0]['id']} in progress in {environment}", status=409)
        row = {
            "id": f"dep-{len(self.rows) + 1}",
            "name": name,
            "environment": environment,
            "image": image,
            "status": "pending",
            "rollback_of": rollback_of,
            "history": [{"status": "pending", "at": now()}],
        }
        self.rows.append(row)
        return row
```

The implementation calls `DeployError`, `len`, `now`, `self.rows.append`, `self.validate`. In an interview, trace those calls in execution order using a fixture input.

## 4. What responsibility does `rollback` have?

`rollback(self, deployment_id)` is defined in [`src/deploys/store.py`](src/deploys/store.py#L82).

Its return expressions include:

- `self.create(failed['name'], failed['environment'], earlier[-1]['image'], rollback_of=failed['id'])`

It uses `DeployError`, `failed['id'].split`, `int`, `row['id'].split`, `self.create`, `self.get`. This is the code path I would compare against the caller to explain responsibility boundaries.

## 5. What input validation and failure behavior are implemented?

Explicit failure paths include:

- `HTTPException(status_code=exc.status, detail=str(exc))` in [`src/deploys/main.py`](src/deploys/main.py#L27).
- `DeployError('deployment not found', status=404)` in [`src/deploys/store.py`](src/deploys/store.py#L65).
- `DeployError('prod is recorded by a pull request, not this form')` in [`src/deploys/store.py`](src/deploys/store.py#L34).
- `DeployError('environment must be dev or staging')` in [`src/deploys/store.py`](src/deploys/store.py#L36).
- `DeployError('name must be lowercase letters, digits, and dashes')` in [`src/deploys/store.py`](src/deploys/store.py#L38).
- `DeployError('image must be repository:tag')` in [`src/deploys/store.py`](src/deploys/store.py#L40).
- `DeployError('pin a tag; latest is refused')` in [`src/deploys/store.py`](src/deploys/store.py#L42).

I would test both the condition that reaches each exception and the caller that translates it. An explicit raise does not mean every malformed input or dependency failure is handled.

## 6. Which test would you use to demonstrate correctness?

[`tests/test_deploys.py`](tests/test_deploys.py#L22) contains `test_prod_is_refused_and_dev_is_listed`:

```python
def test_prod_is_refused_and_dev_is_listed():
    assert deploy(environment="prod").status_code == 422
    created = deploy().json()
    assert created["id"] == "dep-1"
    assert created["status"] == "pending"
    assert client.get("/deployments").json()["deployments"][0]["name"] == "billing"
```

This is a concrete regression example from the repository. Its assertions establish that case; they do not establish behavior for every input or under production load.

## 7. What HTTP interface does the code expose?

- `GET /healthz` → `healthz` in [`src/deploys/main.py`](src/deploys/main.py#L31).
- `GET /deployments` → `list_deployments` in [`src/deploys/main.py`](src/deploys/main.py#L36).
- `POST /deployments` → `create_deployment` in [`src/deploys/main.py`](src/deploys/main.py#L41).
- `GET /deployments/{deployment_id}` → `get_deployment` in [`src/deploys/main.py`](src/deploys/main.py#L46).
- `POST /deployments/{deployment_id}/status` → `move_deployment` in [`src/deploys/main.py`](src/deploys/main.py#L51).
- `POST /deployments/{deployment_id}/rollback` → `rollback_deployment` in [`src/deploys/main.py`](src/deploys/main.py#L56).

These are literal decorators. Application/router prefixes, authentication, and middleware must be checked in the corresponding setup code.

## 8. Where does state live, and what happens with multiple workers?

Module-level containers include `ENVIRONMENTS`, `TRANSITIONS` in [`src/deploys/store.py`](src/deploys/store.py).

These containers belong to a Python process. Inspect which are constant fixtures and which are mutated. Mutable process state needs an explicit shared-storage or synchronization strategy before multiple workers can provide consistent behavior.

## 9. How would another engineer reproduce your walkthrough?

Start from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

These commands follow repository manifests; environment setup and command results still need to be checked on the target machine.

## 10. What does automation verify, and what does it not prove?

Inspect [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for triggers, permissions, and job commands. I would name the checks that those definitions run and show the latest run separately. A workflow definition alone does not establish a successful deployment, security review, or production SLO.

## 11. How would you present this project in a Forward Deployed Engineer interview?

Start with the user and operational problem described in [`README.md`](README.md). Explain one constraint that changes the implementation, show the linked code or example, and walk through a success case and a failure case. Agree on a measurable acceptance criterion before expanding the solution, and leave a handoff with data boundaries and rollback ownership. Any proposed production or business metric should be identified as a target until measured.

## 12. What is the input-to-output contract of `create`?

In [`src/deploys/store.py`](src/deploys/store.py#L44), `create(self, name, environment, image, rollback_of=None)` receives the inputs. The function computes these intermediate values:

- `active = [row for row in self.rows if row['name'] == name and row['environment'] == environment and (row['status'] in {'pending', 'running'})]`
- `row = {'id': f'dep-{len(self.rows) + 1}', 'name': name, 'environment': environment, 'image': image, 'status': 'pending', 'rollback_of': rollback_of, 'history': [{'status': 'pending', 'at': now()}]}`

Its result is defined by:

- `row`

## 13. Which decision rules or boundary conditions should an interviewer challenge?

The implementation in [`src/deploys/store.py`](src/deploys/store.py#L44) branches on:

- `active`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.

## 14. What does `web/src/App.tsx` own?

[`web/src/App.tsx`](web/src/App.tsx) defines `App`, `load`, `send`, `submit`. Its imports include `react`.

Trace these definitions and imports to explain the module boundary. Relative imports identify project code; package imports should be checked against the nearest manifest.
