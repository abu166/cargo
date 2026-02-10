from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.domain import schemas
from app.domain.models import Shipment
from app.infrastructure.db import create_session_factory, Base
from app.infrastructure import repositories
from app.application import services
from shared.config import get_env
from shared.security import decode_token
from shared.shipment_status import ShipmentStatus
from shared.roles import normalize_roles, ROLE_ADMIN, ROLE_OPERATOR, ROLE_AGENT, ROLE_WMS


router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

DATABASE_URL = get_env("DATABASE_URL")
JWT_SECRET = get_env("JWT_SECRET")
JWT_ALGORITHM = get_env("JWT_ALGORITHM", "HS256")

engine, SessionLocal = create_session_factory(DATABASE_URL)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(token, JWT_SECRET, JWT_ALGORITHM)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    roles = set(normalize_roles(payload.get("roles", "")))
    return {"username": payload.get("sub"), "roles": roles}


def require_roles(required: set[str]):
    def _checker(user = Depends(get_current_user)):
        if not required.intersection(user["roles"]):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user
    return _checker


@router.post("/shipments", response_model=schemas.ShipmentOut)
def create_shipment(payload: schemas.ShipmentCreate, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_AGENT, ROLE_ADMIN, ROLE_OPERATOR}))):
    shipment = Shipment(
        client_id=payload.client_id,
        origin_station=payload.origin_station,
        destination_station=payload.destination_station,
        weight_kg=payload.weight_kg,
        length_cm=payload.length_cm,
        width_cm=payload.width_cm,
        height_cm=payload.height_cm,
        status=ShipmentStatus.CREATED.value,
        shipment_id="",
    )
    created = services.create_shipment(db, shipment)
    return schemas.ShipmentOut(
        id=created.id,
        shipment_id=created.shipment_id,
        client_id=created.client_id,
        origin_station=created.origin_station,
        destination_station=created.destination_station,
        weight_kg=created.weight_kg,
        length_cm=created.length_cm,
        width_cm=created.width_cm,
        height_cm=created.height_cm,
        status=ShipmentStatus(created.status),
        created_at=created.created_at,
    )


@router.get("/shipments", response_model=list[schemas.ShipmentOut])
def list_shipments(db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_AGENT, ROLE_ADMIN, ROLE_OPERATOR}))):
    shipments = repositories.list_shipments(db)
    return [schemas.ShipmentOut(
        id=s.id,
        shipment_id=s.shipment_id,
        client_id=s.client_id,
        origin_station=s.origin_station,
        destination_station=s.destination_station,
        weight_kg=s.weight_kg,
        length_cm=s.length_cm,
        width_cm=s.width_cm,
        height_cm=s.height_cm,
        status=ShipmentStatus(s.status),
        created_at=s.created_at,
    ) for s in shipments]


@router.get("/shipments/{shipment_id}", response_model=schemas.ShipmentOut)
def get_shipment(shipment_id: int, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_AGENT, ROLE_ADMIN, ROLE_OPERATOR}))):
    shipment = repositories.get_shipment(db, shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return schemas.ShipmentOut(
        id=shipment.id,
        shipment_id=shipment.shipment_id,
        client_id=shipment.client_id,
        origin_station=shipment.origin_station,
        destination_station=shipment.destination_station,
        weight_kg=shipment.weight_kg,
        length_cm=shipment.length_cm,
        width_cm=shipment.width_cm,
        height_cm=shipment.height_cm,
        status=ShipmentStatus(shipment.status),
        created_at=shipment.created_at,
    )


@router.put("/shipments/{shipment_id}/cancel")
def cancel_shipment(shipment_id: int, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_ADMIN}))):
    shipment = repositories.get_shipment(db, shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    shipment.status = ShipmentStatus.CLOSED.value
    db.commit()
    return {"status": "cancelled"}


@router.post("/shipments/{shipment_id}/qr", response_model=schemas.QRResponse)
def generate_qr(shipment_id: int, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_AGENT, ROLE_ADMIN, ROLE_OPERATOR}))):
    shipment = repositories.get_shipment(db, shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    qr = services.create_qr(db, shipment)
    try:
        services.update_status(db, shipment, ShipmentStatus.QR_GENERATED)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return schemas.QRResponse(id=qr.id, qr_base64=qr.qr_base64, created_at=qr.created_at)


@router.post("/shipments/{shipment_id}/status", response_model=schemas.ShipmentOut)
def update_status(shipment_id: int, payload: schemas.StatusUpdate, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_ADMIN, ROLE_OPERATOR, ROLE_AGENT}))):
    shipment = repositories.get_shipment(db, shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    try:
        updated = services.update_status(db, shipment, payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return schemas.ShipmentOut(
        id=updated.id,
        shipment_id=updated.shipment_id,
        client_id=updated.client_id,
        origin_station=updated.origin_station,
        destination_station=updated.destination_station,
        weight_kg=updated.weight_kg,
        length_cm=updated.length_cm,
        width_cm=updated.width_cm,
        height_cm=updated.height_cm,
        status=ShipmentStatus(updated.status),
        created_at=updated.created_at,
    )


@router.post("/documents/generate", response_model=list[schemas.DocumentOut])
def generate_docs(payload: schemas.DocumentGenerate, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_AGENT, ROLE_ADMIN, ROLE_OPERATOR}))):
    shipment = repositories.get_shipment(db, payload.shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    docs = services.generate_documents(db, shipment, payload.doc_types)
    try:
        services.update_status(db, shipment, ShipmentStatus.DOCUMENTS_CREATED)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return [schemas.DocumentOut(
        id=d.id,
        shipment_id=d.shipment_id,
        doc_type=d.doc_type,
        content=d.content,
        created_at=d.created_at,
    ) for d in docs]


@router.get("/documents/{doc_id}", response_model=schemas.DocumentOut)
def get_document(doc_id: int, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_AGENT, ROLE_ADMIN, ROLE_OPERATOR}))):
    doc = repositories.get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return schemas.DocumentOut(
        id=doc.id,
        shipment_id=doc.shipment_id,
        doc_type=doc.doc_type,
        content=doc.content,
        created_at=doc.created_at,
    )


@router.post("/scan", response_model=schemas.ScanOut)
def scan(payload: schemas.ScanCreate, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_OPERATOR, ROLE_ADMIN, ROLE_AGENT}))):
    shipment = repositories.get_shipment(db, payload.shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    scan_event = services.register_scan(db, shipment, payload.scanned_by, payload.location)
    return schemas.ScanOut(
        id=scan_event.id,
        shipment_id=scan_event.shipment_id,
        scanned_by=scan_event.scanned_by,
        location=scan_event.location,
        created_at=scan_event.created_at,
    )


@router.post("/shipments/{shipment_id}/dropoff/confirm", response_model=schemas.ShipmentOut)
def confirm_dropoff(shipment_id: int, payload: schemas.DropoffConfirm, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_WMS, ROLE_ADMIN, ROLE_AGENT}))):
    shipment = repositories.get_shipment(db, shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    shipment.weight_kg = payload.weight_kg
    shipment.length_cm = payload.length_cm
    shipment.width_cm = payload.width_cm
    shipment.height_cm = payload.height_cm
    updated = services.update_status(db, shipment, ShipmentStatus.DROPPED_OFF)
    return schemas.ShipmentOut(
        id=updated.id,
        shipment_id=updated.shipment_id,
        client_id=updated.client_id,
        origin_station=updated.origin_station,
        destination_station=updated.destination_station,
        weight_kg=updated.weight_kg,
        length_cm=updated.length_cm,
        width_cm=updated.width_cm,
        height_cm=updated.height_cm,
        status=ShipmentStatus(updated.status),
        created_at=updated.created_at,
    )
