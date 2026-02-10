from datetime import datetime
import json
import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Shipment
from app.socket import sio
from shared.config import get_env
from shared.security import decode_token
from shared.roles import (
    normalize_roles,
    STAFF_ROLES,
    ROLE_ADMIN,
    ROLE_MANAGER,
    ROLE_OPERATOR,
    ROLE_RECEIVER,
    ROLE_CORPORATE,
    ROLE_INDIVIDUAL,
)


router = APIRouter(prefix="/api")

JWT_SECRET = get_env("JWT_SECRET", "supersecret")
JWT_ALGORITHM = get_env("JWT_ALGORITHM", "HS256")
AUTH_URL = get_env("AUTH_URL", "http://auth:8000")

STATIONS_ORDER = ["Шымкент", "Алматы-1", "Қарағанды", "Астана Нұрлы Жол", "Ақтөбе"]


ROLE_MAP = {
    ROLE_ADMIN: "admin",
    ROLE_MANAGER: "manager",
    ROLE_OPERATOR: "operator",
    ROLE_RECEIVER: "receiver",
    ROLE_CORPORATE: "corporate",
    ROLE_INDIVIDUAL: "individual",
}


def _shipment_dict(shipment: Shipment) -> dict:
    return {
        "id": shipment.id,
        "client_id": shipment.client_id,
        "client_name": shipment.client_name,
        "client_email": shipment.client_email,
        "from_station": shipment.from_station,
        "to_station": shipment.to_station,
        "current_station": shipment.current_station,
        "next_station": shipment.next_station,
        "status": shipment.status,
        "departure_date": shipment.departure_date,
        "weight": shipment.weight,
        "dimensions": shipment.dimensions,
        "description": shipment.description,
        "value": shipment.value,
        "cost": shipment.cost,
        "created_at": shipment.created_at.isoformat() if shipment.created_at else None,
        "updated_at": shipment.updated_at.isoformat() if shipment.updated_at else None,
    }


def _calculate_route(origin: str, destination: str) -> list[str]:
    origin_index = STATIONS_ORDER.index(origin) if origin in STATIONS_ORDER else -1
    dest_index = STATIONS_ORDER.index(destination) if destination in STATIONS_ORDER else -1
    if origin_index == -1 or dest_index == -1:
        return [origin, destination]
    if origin_index <= dest_index:
        return STATIONS_ORDER[origin_index : dest_index + 1]
    return list(reversed(STATIONS_ORDER[dest_index : origin_index + 1]))


def _primary_role(roles: list[str]) -> str:
    if not roles:
        return "individual"
    return ROLE_MAP.get(roles[0], roles[0].lower())


def _auth_login(email: str, password: str) -> str:
    with httpx.Client(timeout=5.0) as client:
        response = client.post(
            f"{AUTH_URL}/auth/login",
            json={"username": email, "password": password},
        )
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")
    return response.json()["access_token"]


def _auth_register(email: str, password: str, full_name: str | None, role: str, company: str | None, phone: str | None) -> str:
    with httpx.Client(timeout=5.0) as client:
        response = client.post(
            f"{AUTH_URL}/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": full_name,
                "role": role,
                "company": company,
                "phone": phone,
            },
        )
    if response.status_code != 200:
        detail = response.json().get("detail", "Registration failed")
        raise HTTPException(status_code=response.status_code, detail=detail)
    return response.json()["access_token"]


def _auth_me(token: str) -> dict:
    with httpx.Client(timeout=5.0) as client:
        response = client.get(
            f"{AUTH_URL}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return response.json()


def _auth_users(token: str) -> list[dict]:
    with httpx.Client(timeout=5.0) as client:
        response = client.get(
            f"{AUTH_URL}/users",
            headers={"Authorization": f"Bearer {token}"},
        )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch users")
    return response.json()


def _auth_delete_user(token: str, username: str) -> None:
    with httpx.Client(timeout=5.0) as client:
        response = client.delete(
            f"{AUTH_URL}/users/by-username/{username}",
            headers={"Authorization": f"Bearer {token}"},
        )
    if response.status_code not in (200, 404):
        raise HTTPException(status_code=response.status_code, detail="Failed to delete auth user")


def _get_current_user(request: Request) -> dict:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = auth.replace("Bearer ", "", 1)
    try:
        payload = decode_token(token, JWT_SECRET, JWT_ALGORITHM)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    roles = normalize_roles(payload.get("roles", ""))
    return {"sub": payload.get("sub"), "roles": roles}


def _require_roles(roles: set[str]):
    def _checker(request: Request):
        user = _get_current_user(request)
        if not set(user["roles"]).intersection(roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user
    return _checker


def _user_from_profile(profile: dict) -> dict:
    roles = normalize_roles(profile.get("roles", []))
    role = _primary_role(roles)
    return {
        "id": str(profile.get("id")),
        "name": profile.get("full_name") or profile.get("email"),
        "email": profile.get("email") or profile.get("username"),
        "role": role,
        "company": profile.get("company"),
        "deposit_balance": profile.get("deposit_balance"),
        "contract_number": profile.get("contract_number"),
        "phone": profile.get("phone"),
        "station": profile.get("station"),
        "created_at": profile.get("created_at"),
        "status": "active",
    }


@router.post("/auth/register")
async def register(payload: dict):
    name = payload.get("name")
    email = payload.get("email")
    password = payload.get("password")
    role = payload.get("role") or "individual"
    company = payload.get("company")
    phone = payload.get("phone")

    if not name or not email or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required fields")

    token = _auth_register(email, password, name, role.upper(), company, phone)
    profile = _auth_me(token)
    return {"token": token, "user": _user_from_profile(profile)}


@router.post("/auth/login")
async def login(payload: dict):
    email = payload.get("email")
    password = payload.get("password")
    if not email or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing credentials")

    token = _auth_login(email, password)
    profile = _auth_me(token)
    return {"token": token, "user": _user_from_profile(profile)}


@router.get("/shipments")
async def list_shipments(request: Request, type: str | None = None, station: str | None = None, client_id: str | None = None, db: Session = Depends(get_db)):
    _get_current_user(request)
    query = select(Shipment)
    if client_id:
        query = query.where(Shipment.client_id == client_id)
    if type == "incoming" and station:
        query = query.where(Shipment.next_station == station)
    elif type == "outgoing" and station:
        query = query.where(Shipment.current_station == station).where(Shipment.status.in_(["Принят", "Погружен", "В пути"]))
    elif type == "arrived" and station:
        query = query.where(Shipment.current_station == station).where(Shipment.status == "Прибыл")
    shipments = db.execute(query.order_by(Shipment.created_at.desc())).scalars().all()
    return [_shipment_dict(s) for s in shipments]


@router.get("/shipments/by-station/{station}")
async def list_shipments_by_station(station: str, request: Request, db: Session = Depends(get_db)):
    _get_current_user(request)
    shipments = db.execute(
        select(Shipment)
        .where(Shipment.from_station == station)
        .order_by(Shipment.created_at.desc())
    ).scalars().all()
    return [_shipment_dict(s) for s in shipments]


@router.get("/shipments/{shipment_id}")
async def get_shipment(shipment_id: str, db: Session = Depends(get_db)):
    shipment = db.get(Shipment, shipment_id)
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    return _shipment_dict(shipment)


@router.patch("/shipments/{shipment_id}/status")
async def update_shipment_status(shipment_id: str, payload: dict, request: Request, db: Session = Depends(get_db)):
    _get_current_user(request)
    status_value = payload.get("status")
    if not status_value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing status")

    shipment = db.get(Shipment, shipment_id)
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")

    shipment.status = status_value
    shipment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(shipment)

    await sio.emit("shipment-updated", _shipment_dict(shipment), room=f"station:{shipment.from_station}")
    return _shipment_dict(shipment)


@router.post("/shipments")
async def create_shipment(payload: dict, request: Request, db: Session = Depends(get_db)):
    _get_current_user(request)
    required_fields = ["client_id", "from_station", "to_station"]
    for field in required_fields:
        if not payload.get(field):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing {field}")

    shipment_id = f"SH-{str(int(datetime.utcnow().timestamp() * 1000))[-6:]}"
    route = _calculate_route(payload.get("from_station"), payload.get("to_station"))
    shipment = Shipment(
        id=shipment_id,
        client_id=payload.get("client_id"),
        client_name=payload.get("client_name"),
        client_email=payload.get("client_email"),
        from_station=payload.get("from_station"),
        to_station=payload.get("to_station"),
        current_station=payload.get("from_station"),
        next_station=route[1] if len(route) > 1 else None,
        route=json.dumps(route, ensure_ascii=False),
        status="Принят",
        weight=payload.get("weight"),
        dimensions=payload.get("dimensions"),
        description=payload.get("description"),
        value=payload.get("value"),
        cost=payload.get("cost"),
        departure_date=payload.get("departure_date") or datetime.utcnow().isoformat(),
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    await sio.emit("new-shipment", _shipment_dict(shipment), room=f"station:{shipment.from_station}")
    return _shipment_dict(shipment)


@router.get("/admin/employees")
async def list_employees(request: Request):
    _require_roles({ROLE_ADMIN, ROLE_MANAGER, ROLE_OPERATOR})(request)
    token = request.headers.get("Authorization", "").replace("Bearer ", "", 1)
    users = _auth_users(token)
    employees = [u for u in users if set(normalize_roles(u.get("roles", []))).intersection(STAFF_ROLES)]
    return [_user_from_profile(u) for u in employees]


@router.post("/admin/employees")
async def create_employee(payload: dict, request: Request):
    _require_roles({ROLE_ADMIN, ROLE_MANAGER})(request)
    name = payload.get("name")
    email = payload.get("email")
    password = payload.get("password")
    role = payload.get("role")
    station = payload.get("station")

    if not name or not email or not password or not role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required fields")

    token = request.headers.get("Authorization", "").replace("Bearer ", "", 1)
    with httpx.Client(timeout=5.0) as client:
        response = client.post(
            f"{AUTH_URL}/users",
            json={
                "username": email,
                "password": password,
                "full_name": name,
                "roles": [role.upper()],
                "station": station,
                "email": email,
                "phone": None,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to create auth user")

    profile = response.json()
    return _user_from_profile(profile)


@router.delete("/admin/employees/{employee_id}")
async def delete_employee(employee_id: str, request: Request):
    _require_roles({ROLE_ADMIN})(request)
    token = request.headers.get("Authorization", "").replace("Bearer ", "", 1)
    _auth_delete_user(token, employee_id)
    return {"message": "Employee deleted"}


@router.post("/admin/sync-users")
async def sync_users(request: Request):
    _require_roles({ROLE_ADMIN, ROLE_MANAGER})(request)
    token = request.headers.get("Authorization", "").replace("Bearer ", "", 1)
    users = _auth_users(token)
    return {"count": len(users)}


@router.post("/shipments/{shipment_id}/transit")
async def transit_shipment(shipment_id: str, payload: dict, request: Request, db: Session = Depends(get_db)):
    _require_roles({ROLE_OPERATOR, ROLE_RECEIVER, ROLE_ADMIN})(request)
    shipment = db.get(Shipment, shipment_id)
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")

    current_station = payload.get("current_station")
    if not current_station:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing current_station")

    route = json.loads(shipment.route or "[]")
    next_station = None
    status_value = "В пути"

    if route and current_station in route:
        current_index = route.index(current_station)
        if current_index < len(route) - 1:
            next_station = route[current_index + 1]
        else:
            status_value = "Прибыл"
            next_station = None
    elif current_station == shipment.to_station:
        status_value = "Прибыл"

    if current_station == shipment.from_station:
        if shipment.status == "Принят":
            status_value = "Погружен"
        elif shipment.status == "Погружен":
            status_value = "В пути"

    shipment.current_station = current_station
    shipment.next_station = next_station
    shipment.status = status_value
    shipment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(shipment)

    await sio.emit("shipment-updated", _shipment_dict(shipment), room=f"station:{shipment.from_station}")
    if shipment.next_station:
        await sio.emit("shipment-incoming", _shipment_dict(shipment), room=f"station:{shipment.next_station}")
    return _shipment_dict(shipment)


@router.get("/reports/dashboard")
async def dashboard_report(request: Request, db: Session = Depends(get_db)):
    _require_roles({ROLE_ADMIN, ROLE_MANAGER})(request)
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    shipments = db.execute(select(Shipment)).scalars().all()

    monthly_shipments = [s for s in shipments if s.created_at and s.created_at >= start_of_month]
    completed = [s for s in monthly_shipments if s.status in ("Выдан", "Доставлен")]
    active = [s for s in shipments if s.status not in ("Выдан", "Доставлен")]

    revenue_map: dict[tuple[str, str], float] = {}
    for s in monthly_shipments:
        if s.cost is None:
            continue
        key = (s.from_station, s.to_station)
        revenue_map[key] = revenue_map.get(key, 0.0) + float(s.cost)

    revenue_by_route = [
        {
            "route": f"{k[0]}-{k[1]}",
            "revenue": v,
            "count": len([s for s in monthly_shipments if s.from_station == k[0] and s.to_station == k[1]]),
        }
        for k, v in revenue_map.items()
    ]

    revenue_by_route.sort(key=lambda x: x["revenue"], reverse=True)
    return {
        "monthlyShipments": len(monthly_shipments),
        "completedShipments": len(completed),
        "activeContracts": len(active),
        "revenueByRoute": revenue_by_route[:5],
    }
