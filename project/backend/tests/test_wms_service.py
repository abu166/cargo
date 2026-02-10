import os
from fastapi.testclient import TestClient

from shared.security import create_access_token


os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/wms_test.db")
os.environ.setdefault("JWT_SECRET", "testsecret")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("SHIPMENTS_URL", "http://shipments:8000")

from services.wms.app.main import app  # noqa: E402


def make_headers(roles: str = "WMS"):
    token = create_access_token({"sub": "tester", "roles": roles}, "testsecret", "HS256", 60)
    return {"Authorization": f"Bearer {token}"}


def test_wms_list_cells_and_sessions():
    client = TestClient(app)
    headers = make_headers("WMS")

    warehouses = client.get("/wms/warehouses", headers=headers)
    assert warehouses.status_code == 200

    cells = client.get("/wms/cells", headers=headers)
    assert cells.status_code == 200

    session = client.post("/wms/sessions", json={}, headers=headers)
    assert session.status_code == 200
