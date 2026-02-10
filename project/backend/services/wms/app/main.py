import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.presentation.routes import router, SessionLocal, engine
from app.infrastructure.db import Base
from app.domain.models import Warehouse, StorageCell

app = FastAPI(title="CargoTrans WMS Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.on_event("startup")
def seed_wms():
    for _ in range(20):
        try:
            Base.metadata.create_all(bind=engine)
            break
        except Exception:
            time.sleep(1)
    db = SessionLocal()
    try:
        if not db.query(Warehouse).first():
            warehouse = Warehouse(name="Main Warehouse", location="Station A")
            db.add(warehouse)
            db.commit()
            db.refresh(warehouse)
            cells = [StorageCell(warehouse_id=warehouse.id, code=f"CELL-{i:03d}") for i in range(1, 11)]
            db.add_all(cells)
            db.commit()
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}
