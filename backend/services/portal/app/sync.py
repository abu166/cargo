import logging
import os
import time
import httpx

from shared.roles import normalize_roles


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("portal-sync")

AUTH_URL = os.getenv("AUTH_URL", "http://auth:8000")
ADMIN_USER = os.getenv("ADMIN_USER", "admin@cargo.kz")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
SYNC_INTERVAL_SECONDS = int(os.getenv("SYNC_INTERVAL_SECONDS", "60"))


def _login() -> str:
    with httpx.Client(timeout=5.0) as client:
        resp = client.post(f"{AUTH_URL}/auth/login", json={"username": ADMIN_USER, "password": ADMIN_PASSWORD})
    resp.raise_for_status()
    return resp.json()["access_token"]


def _fetch_users(token: str) -> list[dict]:
    with httpx.Client(timeout=5.0) as client:
        resp = client.get(f"{AUTH_URL}/users", headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    return resp.json()


def _sync_once():
    token = _login()
    users = _fetch_users(token)
    staff_count = sum(1 for u in users if normalize_roles(u.get("roles", [])))
    logger.info("Fetched %s users from auth", len(users))
    logger.info("Sample roles count: %s", staff_count)


def run():
    while True:
        try:
            _sync_once()
        except Exception as exc:
            logger.exception("Sync failed: %s", exc)
        time.sleep(SYNC_INTERVAL_SECONDS)


if __name__ == "__main__":
    run()
