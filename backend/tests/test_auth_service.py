import os
from fastapi.testclient import TestClient


os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/auth_test.db")
os.environ.setdefault("JWT_SECRET", "testsecret")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "60")
os.environ.setdefault("ADMIN_USER", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "admin123")

from services.auth.app.main import app  # noqa: E402


def test_auth_login_and_user_crud():
    client = TestClient(app)

    login = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    create = client.post(
        "/users",
        json={"username": "agent1", "password": "pass", "full_name": "Agent", "roles": ["AGENT"]},
        headers=headers,
    )
    assert create.status_code == 200
    user_id = create.json()["id"]

    users = client.get("/users", headers=headers)
    assert users.status_code == 200
    assert any(u["id"] == user_id for u in users.json())

    update = client.put(f"/users/{user_id}", json={"full_name": "Agent Updated"}, headers=headers)
    assert update.status_code == 200
