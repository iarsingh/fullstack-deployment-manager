import re
from datetime import datetime, timezone

ENVIRONMENTS = {"dev", "staging"}
IMAGE = re.compile(r"^[a-z0-9][a-z0-9./_-]*:[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
TRANSITIONS = {
    "pending": {"running", "cancelled"},
    "running": {"succeeded", "failed"},
    "succeeded": set(),
    "failed": set(),
    "cancelled": set(),
}


class DeployError(ValueError):
    def __init__(self, message, status=422):
        super().__init__(message)
        self.status = status


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self):
        self.rows = []

    def clear(self):
        self.rows.clear()

    def validate(self, name, environment, image):
        if environment == "prod":
            raise DeployError("prod is recorded by a pull request, not this form")
        if environment not in ENVIRONMENTS:
            raise DeployError("environment must be dev or staging")
        if not re.fullmatch(r"[a-z][a-z0-9-]{1,40}", name):
            raise DeployError("name must be lowercase letters, digits, and dashes")
        if not IMAGE.fullmatch(image):
            raise DeployError("image must be repository:tag")
        if image.endswith(":latest"):
            raise DeployError("pin a tag; latest is refused")

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

    def get(self, deployment_id):
        for row in self.rows:
            if row["id"] == deployment_id:
                return row
        raise DeployError("deployment not found", status=404)

    def list(self, environment=None, name=None):
        return [
            row
            for row in self.rows
            if (environment is None or row["environment"] == environment) and (name is None or row["name"] == name)
        ]

    def transition(self, deployment_id, status):
        row = self.get(deployment_id)
        if status not in TRANSITIONS.get(row["status"], set()):
            raise DeployError(f"cannot move {row['id']} from {row['status']} to {status}", status=409)
        row["status"] = status
        row["history"].append({"status": status, "at": now()})
        return row

    def rollback(self, deployment_id):
        failed = self.get(deployment_id)
        if failed["status"] != "failed":
            raise DeployError("only a failed deployment can be rolled back", status=409)
        earlier = [
            row
            for row in self.rows
            if row["name"] == failed["name"]
            and row["environment"] == failed["environment"]
            and row["status"] == "succeeded"
            and int(row["id"].split("-")[1]) < int(failed["id"].split("-")[1])
        ]
        if not earlier:
            raise DeployError("no earlier successful deployment to roll back to", status=409)
        return self.create(failed["name"], failed["environment"], earlier[-1]["image"], rollback_of=failed["id"])
