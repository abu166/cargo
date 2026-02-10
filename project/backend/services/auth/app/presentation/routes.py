from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.domain import schemas
from app.infrastructure.db import create_session_factory, Base
from app.infrastructure import repositories
from app.application import services
from shared.config import get_env
from shared.security import create_access_token, decode_token
from shared.roles import normalize_roles, roles_to_string, ROLE_ADMIN, ROLE_AGENT, ROLE_OPERATOR, ROLE_CORPORATE, ROLE_INDIVIDUAL


router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


DATABASE_URL = get_env("DATABASE_URL")
JWT_SECRET = get_env("JWT_SECRET")
JWT_ALGORITHM = get_env("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(get_env("JWT_EXPIRE_MINUTES", "120"))

engine, SessionLocal = create_session_factory(DATABASE_URL)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(token, JWT_SECRET, JWT_ALGORITHM)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = repositories.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_roles(required: set[str]):
    def _checker(user = Depends(get_current_user)):
        roles = set(normalize_roles(user.roles))
        if not required.intersection(roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user
    return _checker


@router.post("/auth/login", response_model=schemas.Token)
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = services.authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": user.username, "roles": user.roles}, JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES)
    services.log_action(db, user.id, "login")
    return schemas.Token(access_token=token)


@router.post("/auth/register", response_model=schemas.Token)
def register(payload: schemas.RegisterRequest, db: Session = Depends(get_db)):
    existing = repositories.get_user_by_username(db, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    role = payload.role.upper()
    if role not in {ROLE_CORPORATE, ROLE_INDIVIDUAL}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    user = services.register_user(
        db,
        payload.email,
        payload.password,
        payload.full_name,
        [role],
        email=payload.email,
        company=payload.company,
        phone=payload.phone,
    )
    token = create_access_token({"sub": user.username, "roles": user.roles}, JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES)
    return schemas.Token(access_token=token)


@router.get("/auth/me", response_model=schemas.UserOut)
def me(user = Depends(get_current_user)):
    return schemas.UserOut(
        id=user.id,
        username=user.username,
        email=user.email or user.username,
        full_name=user.full_name,
        roles=list(filter(None, normalize_roles(user.roles))),
        is_active=user.is_active,
        station=user.station,
        company=user.company,
        deposit_balance=user.deposit_balance,
        contract_number=user.contract_number,
        phone=user.phone,
        created_at=user.created_at,
    )


@router.post("/auth/logout")
def logout(user = Depends(get_current_user), db: Session = Depends(get_db)):
    services.log_action(db, user.id, "logout")
    return {"status": "ok"}


@router.get("/users", response_model=list[schemas.UserOut])
def list_users(db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_ADMIN}))):
    users = repositories.list_users(db)
    return [schemas.UserOut(
        id=u.id,
        username=u.username,
        email=u.email or u.username,
        full_name=u.full_name,
        roles=list(filter(None, normalize_roles(u.roles))),
        is_active=u.is_active,
        station=u.station,
        company=u.company,
        deposit_balance=u.deposit_balance,
        contract_number=u.contract_number,
        phone=u.phone,
        created_at=u.created_at,
    ) for u in users]


@router.post("/users", response_model=schemas.UserOut)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_ADMIN}))):
    user = services.register_user(
        db,
        payload.username,
        payload.password,
        payload.full_name,
        payload.roles,
        payload.station,
        email=payload.email,
        company=payload.company,
        deposit_balance=payload.deposit_balance,
        contract_number=payload.contract_number,
        phone=payload.phone,
    )
    services.log_action(db, _user.id, "create_user", f"user_id={user.id}")
    return schemas.UserOut(
        id=user.id,
        username=user.username,
        email=user.email or user.username,
        full_name=user.full_name,
        roles=list(filter(None, normalize_roles(user.roles))),
        is_active=user.is_active,
        station=user.station,
        company=user.company,
        deposit_balance=user.deposit_balance,
        contract_number=user.contract_number,
        phone=user.phone,
        created_at=user.created_at,
    )


@router.put("/users/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: int, payload: schemas.UserUpdate, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_ADMIN}))):
    user = repositories.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.roles is not None:
        user.roles = roles_to_string(payload.roles)
    if payload.station is not None:
        user.station = payload.station
    if payload.email is not None:
        user.email = payload.email
    if payload.company is not None:
        user.company = payload.company
    if payload.deposit_balance is not None:
        user.deposit_balance = payload.deposit_balance
    if payload.contract_number is not None:
        user.contract_number = payload.contract_number
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.is_active is not None:
        user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    services.log_action(db, _user.id, "update_user", f"user_id={user.id}")
    return schemas.UserOut(
        id=user.id,
        username=user.username,
        email=user.email or user.username,
        full_name=user.full_name,
        roles=list(filter(None, normalize_roles(user.roles))),
        is_active=user.is_active,
        station=user.station,
        company=user.company,
        deposit_balance=user.deposit_balance,
        contract_number=user.contract_number,
        phone=user.phone,
        created_at=user.created_at,
    )


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_ADMIN}))):
    user = repositories.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    repositories.delete_user(db, user)
    services.log_action(db, _user.id, "delete_user", f"user_id={user_id}")
    return {"status": "deleted"}


@router.delete("/users/by-username/{username}")
def delete_user_by_username(username: str, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_ADMIN}))):
    user = repositories.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    repositories.delete_user(db, user)
    services.log_action(db, _user.id, "delete_user", f"username={username}")
    return {"status": "deleted"}


@router.post("/clients", response_model=schemas.ClientOut)
def create_client(payload: schemas.ClientCreate, db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_AGENT, ROLE_ADMIN, ROLE_OPERATOR}))):
    client = services.register_client(db, payload.full_name, payload.document_id, payload.phone)
    services.log_action(db, _user.id, "create_client", f"client_id={client.id}")
    return schemas.ClientOut(
        id=client.id,
        full_name=client.full_name,
        document_id=client.document_id,
        phone=client.phone,
        created_at=client.created_at,
    )


@router.get("/clients", response_model=list[schemas.ClientOut])
def list_clients(db: Session = Depends(get_db), _user = Depends(require_roles({"AGENT", "ADMIN", "OPERATOR"}))):
    clients = repositories.list_clients(db)
    return [schemas.ClientOut(
        id=c.id,
        full_name=c.full_name,
        document_id=c.document_id,
        phone=c.phone,
        created_at=c.created_at,
    ) for c in clients]


@router.get("/audit/logs", response_model=list[schemas.AuditOut])
def audit_logs(db: Session = Depends(get_db), _user = Depends(require_roles({ROLE_ADMIN}))):
    logs = repositories.list_audit(db)
    return [schemas.AuditOut(
        id=l.id,
        user_id=l.user_id,
        action=l.action,
        details=l.details,
        created_at=l.created_at,
    ) for l in logs]
