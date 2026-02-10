from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from app.db import Base, engine, SessionLocal
from app.routes import router
from app.socket import sio


fastapi_app = FastAPI(title="CargoTrans Portal Service")

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@fastapi_app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


fastapi_app.include_router(router)

app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
