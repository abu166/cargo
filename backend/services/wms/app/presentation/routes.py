from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.domain import schemas
from app.domain.models import StorageCell
from app.infrastructure.db import create_session_factory, Base
from app.infrastructure import repositories
from app.application import services
from shared.config import get_env
from shared.security import decode_token
from shared.roles import normalize_roles, ROLE_WMS, ROLE_ADMIN, ROLE_OPERATOR
from shared.shipment_status import ShipmentStatus


router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

DATABASE_URL = get_env("DATABASE_URL")
JWT_SECRET = get_env("JWT_SECRET")
JWT_ALGORITHM = get_env("JWT_ALGORITHM", "HS256")
SHIPMENTS_URL = get_env("SHIPMENTS_URL", "http://shipments:8000")

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


def get_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    return auth.replace("Bearer ", "", 1)


@router.get("/wms/warehouses", response_model=list[schemas.WarehouseOut])
def list_warehouses(db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_WMS, ROLE_ADMIN, ROLE_OPERATOR}))):
    warehouses = repositories.list_warehouses(db)
    return [schemas.WarehouseOut(id=w.id, name=w.name, location=w.location, created_at=w.created_at) for w in warehouses]


@router.get("/wms/cells", response_model=list[schemas.CellOut])
def list_cells(status: str | None = None, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_WMS, ROLE_ADMIN, ROLE_OPERATOR}))):
    cells = repositories.list_cells(db, status)
    return [schemas.CellOut(id=c.id, warehouse_id=c.warehouse_id, code=c.code, status=c.status, created_at=c.created_at) for c in cells]


@router.post("/wms/sessions", response_model=schemas.SessionOut)
def create_session(payload: schemas.SessionCreate, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_WMS, ROLE_ADMIN, ROLE_OPERATOR}))):
    session = services.create_cell_session(db, payload.shipment_id)
    return schemas.SessionOut(
        id=session.id,
        cell_id=session.cell_id,
        shipment_id=session.shipment_id,
        status=session.status,
        created_at=session.created_at,
        opened_at=session.opened_at,
        closed_at=session.closed_at,
    )


@router.post("/wms/sessions/{session_id}/open-cell", response_model=schemas.SessionOut)
def open_cell(session_id: int, cell_id: int, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_WMS, ROLE_ADMIN, ROLE_OPERATOR}))):
    session = repositories.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    cell = repositories.get_cell(db, cell_id)
    if not cell:
        raise HTTPException(status_code=404, detail="Cell not found")
    if cell.status != "FREE":
        raise HTTPException(status_code=400, detail="Cell not free")
    session.cell_id = cell.id
    session.opened_at = datetime.utcnow()
    session.status = "OPENED"
    cell.status = "OCCUPIED"
    db.commit()
    return schemas.SessionOut(
        id=session.id,
        cell_id=session.cell_id,
        shipment_id=session.shipment_id,
        status=session.status,
        created_at=session.created_at,
        opened_at=session.opened_at,
        closed_at=session.closed_at,
    )


@router.post("/wms/events", response_model=schemas.EventOut)
def create_event(payload: schemas.EventCreate, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_WMS, ROLE_ADMIN, ROLE_OPERATOR}))):
    event = services.log_event(db, payload.session_id, payload.event_type, payload.payload)
    return schemas.EventOut(
        id=event.id,
        session_id=event.session_id,
        event_type=event.event_type,
        payload=event.payload,
        created_at=event.created_at,
    )


@router.post("/wms/cells/open")
def open_cell_manual(cell_id: int, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_WMS, ROLE_ADMIN, ROLE_OPERATOR}))):
    cell = repositories.get_cell(db, cell_id)
    if not cell:
        raise HTTPException(status_code=404, detail="Cell not found")
    cell.status = "OCCUPIED"
    repositories.update_cell(db, cell)
    return {"status": "opened"}


@router.post("/wms/cells/close")
def close_cell_manual(cell_id: int, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_WMS, ROLE_ADMIN, ROLE_OPERATOR}))):
    cell = repositories.get_cell(db, cell_id)
    if not cell:
        raise HTTPException(status_code=404, detail="Cell not found")
    cell.status = "FREE"
    repositories.update_cell(db, cell)
    return {"status": "closed"}


@router.post("/wms/assign")
def assign_shipment(cell_id: int, shipment_id: int, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_WMS, ROLE_ADMIN, ROLE_OPERATOR}))):
    cell = repositories.get_cell(db, cell_id)
    if not cell:
        raise HTTPException(status_code=404, detail="Cell not found")
    cell.status = "OCCUPIED"
    repositories.update_cell(db, cell)
    return {"status": "assigned", "shipment_id": shipment_id}


@router.post("/wms/remove")
def remove_shipment(cell_id: int, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_WMS, ROLE_ADMIN, ROLE_OPERATOR}))):
    cell = repositories.get_cell(db, cell_id)
    if not cell:
        raise HTTPException(status_code=404, detail="Cell not found")
    cell.status = "FREE"
    repositories.update_cell(db, cell)
    return {"status": "removed"}


@router.post("/measurements", response_model=schemas.MeasurementOut)
def create_measurement(payload: schemas.MeasurementCreate, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_WMS, ROLE_ADMIN, ROLE_OPERATOR}))):
    measurement = services.record_measurement(
        db,
        payload.shipment_id,
        payload.weight_kg,
        payload.length_cm,
        payload.width_cm,
        payload.height_cm,
        payload.discrepancy_flag,
    )
    return schemas.MeasurementOut(
        id=measurement.id,
        shipment_id=measurement.shipment_id,
        weight_kg=measurement.weight_kg,
        length_cm=measurement.length_cm,
        width_cm=measurement.width_cm,
        height_cm=measurement.height_cm,
        discrepancy_flag=measurement.discrepancy_flag,
        created_at=measurement.created_at,
    )


@router.post("/routes/plan", response_model=schemas.RoutePlanOut)
def create_route(payload: schemas.RoutePlanCreate, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_ADMIN, ROLE_OPERATOR}))):
    plan = services.create_route_plan(db, payload.origin_station, payload.destination_station, payload.wagons_count)
    return schemas.RoutePlanOut(
        id=plan.id,
        origin_station=plan.origin_station,
        destination_station=plan.destination_station,
        wagons_count=plan.wagons_count,
        status=plan.status,
        created_at=plan.created_at,
    )


@router.post("/routes/{plan_id}/approve", response_model=schemas.RoutePlanOut)
def approve_route(plan_id: int, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_ADMIN, ROLE_OPERATOR}))):
    plan = repositories.get_route_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Route plan not found")
    plan = services.approve_route_plan(db, plan)
    return schemas.RoutePlanOut(
        id=plan.id,
        origin_station=plan.origin_station,
        destination_station=plan.destination_station,
        wagons_count=plan.wagons_count,
        status=plan.status,
        created_at=plan.created_at,
    )


@router.post("/transport/load")
def transport_load(payload: schemas.TransportAction, request: Request, _user = Depends(require_roles({ROLE_OPERATOR, ROLE_ADMIN}))):
    token = get_token(request)
    services.advance_shipment_status(SHIPMENTS_URL, token, payload.shipment_id, [ShipmentStatus.LOADED])
    return {"status": "loaded"}


@router.post("/transport/unload")
def transport_unload(payload: schemas.TransportAction, request: Request, _user = Depends(require_roles({ROLE_OPERATOR, ROLE_ADMIN}))):
    token = get_token(request)
    services.advance_shipment_status(SHIPMENTS_URL, token, payload.shipment_id, [ShipmentStatus.LOADED, ShipmentStatus.IN_TRANSIT])
    return {"status": "in_transit"}


@router.post("/transport/arrive")
def transport_arrive(payload: schemas.TransportAction, request: Request, _user = Depends(require_roles({ROLE_OPERATOR, ROLE_ADMIN}))):
    token = get_token(request)
    services.advance_shipment_status(
        SHIPMENTS_URL,
        token,
        payload.shipment_id,
        [ShipmentStatus.LOADED, ShipmentStatus.IN_TRANSIT, ShipmentStatus.ARRIVED],
    )
    return {"status": "arrived"}


@router.post("/delivery/ready")
def delivery_ready(payload: schemas.DeliveryAction, request: Request, _user = Depends(require_roles({ROLE_OPERATOR, ROLE_ADMIN}))):
    token = get_token(request)
    services.advance_shipment_status(
        SHIPMENTS_URL,
        token,
        payload.shipment_id,
        [ShipmentStatus.LOADED, ShipmentStatus.IN_TRANSIT, ShipmentStatus.ARRIVED, ShipmentStatus.NOTIFIED],
    )
    return {"status": "notified"}


@router.post("/delivery/confirm")
def delivery_confirm(payload: schemas.DeliveryAction, request: Request, _user = Depends(require_roles({ROLE_OPERATOR, ROLE_ADMIN}))):
    token = get_token(request)
    services.advance_shipment_status(
        SHIPMENTS_URL,
        token,
        payload.shipment_id,
        [
            ShipmentStatus.LOADED,
            ShipmentStatus.IN_TRANSIT,
            ShipmentStatus.ARRIVED,
            ShipmentStatus.NOTIFIED,
            ShipmentStatus.ISSUED,
            ShipmentStatus.CLOSED,
        ],
    )
    return {"status": "closed"}


@router.post("/scan")
def scan(payload: schemas.ScanCreate, request: Request, _user = Depends(require_roles({ROLE_OPERATOR, ROLE_ADMIN}))):
    token = get_token(request)
    services.forward_scan(SHIPMENTS_URL, token, payload.shipment_id, payload.scanned_by, payload.location)
    return {"status": "scanned"}


@router.post("/wms/dropoff/confirm")
def dropoff_confirm(
    request: Request,
    session_id: int,
    shipment_id: int,
    weight_kg: float,
    length_cm: float | None = None,
    width_cm: float | None = None,
    height_cm: float | None = None,
    db: Session = Depends(get_db),
    _user = Depends(require_roles({ROLE_WMS, ROLE_ADMIN})),
):
    token = get_token(request)
    services.confirm_dropoff(SHIPMENTS_URL, token, shipment_id, weight_kg, length_cm, width_cm, height_cm)
    services.log_event(db, session_id, "dropoff_confirmed", f"shipment_id={shipment_id}")
    return {"status": "dropoff_confirmed"}
