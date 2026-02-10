import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.presentation.routes import router, engine
from app.infrastructure.db import Base

app = FastAPI(title="CargoTrans Shipments Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

@app.on_event("startup")
def init_db():
    for _ in range(20):
        try:
            Base.metadata.create_all(bind=engine)
            break
        except Exception:
            time.sleep(1)


@app.get("/health")
def health():
    return {"status": "ok"}
