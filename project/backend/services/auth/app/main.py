import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.presentation.routes import router, SessionLocal, engine
from app.infrastructure.db import Base
from app.infrastructure import repositories
from app.application import services
from shared.config import get_env

app = FastAPI(title="CargoTrans Auth Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.on_event("startup")
def seed_admin():
    for _ in range(20):
        try:
            Base.metadata.create_all(bind=engine)
            break
        except Exception:
            time.sleep(1)
    username = get_env("ADMIN_USER", "admin")
    password = get_env("ADMIN_PASSWORD", "admin123")
    db = SessionLocal()
    try:
        existing = repositories.get_user_by_username(db, username)
        if not existing:
            services.register_user(db, username, password, "System Admin", ["ADMIN"], email=username)
        demo_users = [
            ("operator@mail.kz", "demo", "Оператор", ["OPERATOR"], "Алматы-1"),
            ("corporate@mail.kz", "demo", "Корпоративный клиент", ["CORPORATE"], None),
            ("user@mail.kz", "demo", "Физическое лицо", ["INDIVIDUAL"], None),
            ("receiver@mail.kz", "demo", "Приемосдатчик", ["RECEIVER", "OPERATOR"], "Алматы-1"),
            ("wms@mail.kz", "demo", "WMS", ["WMS"], None),
            ("cashier@mail.kz", "demo", "Кассир", ["CASHIER"], None),
            ("accountant@mail.kz", "demo", "Бухгалтер", ["ACCOUNTANT"], None),
        ]
        for demo_username, demo_password, full_name, roles, station in demo_users:
            if not repositories.get_user_by_username(db, demo_username):
                services.register_user(db, demo_username, demo_password, full_name, roles, station, email=demo_username)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}
