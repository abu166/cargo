from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.domain import schemas
from app.domain.models import Payment
from app.infrastructure.db import create_session_factory, Base
from app.infrastructure import repositories
from app.application import services
from shared.config import get_env
from shared.shipment_status import ShipmentStatus
import httpx
from shared.security import decode_token
from shared.roles import normalize_roles, ROLE_ADMIN, ROLE_ACCOUNTANT, ROLE_AGENT, ROLE_CASHIER, ROLE_OPERATOR


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

@router.post("/tariffs", response_model=schemas.TariffOut)
def create_tariff(payload: schemas.TariffCreate, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_ADMIN, ROLE_ACCOUNTANT}))):
    tariff = services.create_tariff(db, payload.name, payload.base_rate, payload.per_kg_rate)
    return schemas.TariffOut(
        id=tariff.id,
        name=tariff.name,
        base_rate=tariff.base_rate,
        per_kg_rate=tariff.per_kg_rate,
        created_at=tariff.created_at,
    )


@router.get("/tariffs", response_model=list[schemas.TariffOut])
def list_tariffs(db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_ADMIN, ROLE_ACCOUNTANT, ROLE_AGENT}))):
    tariffs = repositories.list_tariffs(db)
    return [schemas.TariffOut(
        id=t.id,
        name=t.name,
        base_rate=t.base_rate,
        per_kg_rate=t.per_kg_rate,
        created_at=t.created_at,
    ) for t in tariffs]


@router.post("/tariffs/calc", response_model=schemas.TariffCalcOut)
def calc_tariff(payload: schemas.TariffCalc, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_ADMIN, ROLE_ACCOUNTANT, ROLE_AGENT}))):
    try:
        amount = services.calculate_amount(db, payload.tariff_id, payload.weight_kg)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return schemas.TariffCalcOut(tariff_id=payload.tariff_id, amount=amount)


@router.post("/payments", response_model=schemas.PaymentOut)
def create_payment(payload: schemas.PaymentCreate, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_CASHIER, ROLE_ADMIN, ROLE_OPERATOR}))):
    payment = services.create_payment(db, payload.shipment_id, payload.amount, payload.method)
    return schemas.PaymentOut(
        id=payment.id,
        shipment_id=payment.shipment_id,
        amount=payment.amount,
        status=payment.status,
        method=payment.method,
        created_at=payment.created_at,
    )


@router.put("/payments/{payment_id}", response_model=schemas.PaymentOut)
def update_payment(payment_id: int, payload: schemas.PaymentUpdate, request: Request, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_CASHIER, ROLE_ADMIN, ROLE_OPERATOR}))):
    payment = repositories.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    payment = services.update_payment_status(db, payment, payload.status)
    if payload.status.upper() == "PAID":
        token = get_token(request)
        with httpx.Client(timeout=5.0) as client:
            response = client.post(
                f"{SHIPMENTS_URL}/shipments/{payment.shipment_id}/status",
                json={"status": ShipmentStatus.PAID.value},
                headers={"Authorization": f"Bearer {token}"},
            )
        response.raise_for_status()
    return schemas.PaymentOut(
        id=payment.id,
        shipment_id=payment.shipment_id,
        amount=payment.amount,
        status=payment.status,
        method=payment.method,
        created_at=payment.created_at,
    )


@router.get("/payments", response_model=list[schemas.PaymentOut])
def list_payments(db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_ACCOUNTANT, ROLE_ADMIN}))):
    payments = repositories.list_payments(db)
    return [schemas.PaymentOut(
        id=p.id,
        shipment_id=p.shipment_id,
        amount=p.amount,
        status=p.status,
        method=p.method,
        created_at=p.created_at,
    ) for p in payments]


@router.get("/accounting/fo-3", response_model=schemas.FO3Report)
def fo3_report(db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_ACCOUNTANT, ROLE_ADMIN}))):
    payments = repositories.list_payments(db)
    total = sum(p.amount for p in payments if p.status == "PAID")
    count = sum(1 for p in payments if p.status == "PAID")
    return schemas.FO3Report(total_amount=total, payments_count=count)
