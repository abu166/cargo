import os
from fastapi.testclient import TestClient

from shared.security import create_access_token


os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/finance_test.db")
os.environ.setdefault("JWT_SECRET", "testsecret")
os.environ.setdefault("JWT_ALGORITHM", "HS256")

from services.finance.app.main import app  # noqa: E402


def make_headers(roles: str = "ADMIN"):
    token = create_access_token({"sub": "tester", "roles": roles}, "testsecret", "HS256", 60)
    return {"Authorization": f"Bearer {token}"}


def test_tariff_and_payment_flow():
    client = TestClient(app)
    headers_admin = make_headers("ADMIN")

    tariff = client.post("/tariffs", json={"name": "Base", "base_rate": 100, "per_kg_rate": 10}, headers=headers_admin)
    assert tariff.status_code == 200
    tariff_id = tariff.json()["id"]

    calc = client.post("/tariffs/calc", json={"tariff_id": tariff_id, "weight_kg": 2}, headers=headers_admin)
    assert calc.status_code == 200

    headers_cashier = make_headers("CASHIER")
    payment = client.post("/payments", json={"shipment_id": 1, "amount": 120, "method": "CASH"}, headers=headers_cashier)
    assert payment.status_code == 200

    update = client.put(f"/payments/{payment.json()['id']}", json={"status": "PENDING"}, headers=headers_cashier)
    assert update.status_code == 200
