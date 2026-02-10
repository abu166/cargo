import os
from fastapi.testclient import TestClient

from shared.security import create_access_token


os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/shipments_test.db")
os.environ.setdefault("JWT_SECRET", "testsecret")
os.environ.setdefault("JWT_ALGORITHM", "HS256")

from services.shipments.app.main import app  # noqa: E402


def make_headers(roles: str = "AGENT"):
    token = create_access_token({"sub": "tester", "roles": roles}, "testsecret", "HS256", 60)
    return {"Authorization": f"Bearer {token}"}


def test_shipment_flow():
    client = TestClient(app)
    headers = make_headers("AGENT")

    create = client.post(
        "/shipments",
        json={"origin_station": "A", "destination_station": "B", "weight_kg": 10.0},
        headers=headers,
    )
    assert create.status_code == 200
    shipment_id = create.json()["id"]

    status_calc = client.post(
        f"/shipments/{shipment_id}/status",
        json={"status": "TARIFF_CALCULATED"},
        headers=headers,
    )
    assert status_calc.status_code == 200

    status_paid = client.post(
        f"/shipments/{shipment_id}/status",
        json={"status": "PAID"},
        headers=headers,
    )
    assert status_paid.status_code == 200

    qr = client.post(f"/shipments/{shipment_id}/qr", headers=headers)
    assert qr.status_code == 200

    docs = client.post(
        "/documents/generate",
        json={"shipment_id": shipment_id, "doc_types": ["LU-12", "LU-63"]},
        headers=headers,
    )
    assert docs.status_code == 200
