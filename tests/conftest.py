import os
import tempfile

import pytest

# Point the app at a throwaway database and media folder before it is imported.
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["MEDIA_DIR"] = f"{_tmp}/media"
os.environ["ADMIN_PASSWORD"] = "test-admin"
for k in ("RAILWAY_ENVIRONMENT_NAME", "RAILWAY_ENVIRONMENT", "RAILWAY_PROJECT_ID", "RAILWAY_VOLUME_MOUNT_PATH"):
    os.environ.pop(k, None)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


REGISTER = {"circumstance": "register", "dogName": "Biscuit", "breed": "Cavalier", "tier": "petite", "pose": "Resting",
            "story": "", "name": "Ann Lee", "email": "ann@example.com", "phone": "212 555 0100", "city": "Rye",
            "contact": "Telephone", "vet": ""}


@pytest.fixture
def token(client):
    res = client.post("/api/commissions", json=REGISTER)
    assert res.status_code == 201
    return res.json()["likeness_url"].rsplit("/", 1)[1]
