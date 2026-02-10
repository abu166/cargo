from sqlalchemy.orm import Session

from app.domain.models import User, AuditLog, Client
from app.infrastructure import repositories
from shared.security import hash_password, verify_password
from shared.roles import normalize_roles, roles_to_string


def register_user(
    session: Session,
    username: str,
    password: str,
    full_name: str | None,
    roles: list[str],
    station: str | None = None,
    email: str | None = None,
    company: str | None = None,
    deposit_balance: float | None = None,
    contract_number: str | None = None,
    phone: str | None = None,
) -> User:
    role_string = roles_to_string(roles)
    user = User(
        username=username,
        password_hash=hash_password(password),
        full_name=full_name,
        roles=role_string,
        station=station,
        email=email,
        company=company,
        deposit_balance=deposit_balance,
        contract_number=contract_number,
        phone=phone,
    )
    return repositories.create_user(session, user)


def authenticate_user(session: Session, username: str, password: str) -> User | None:
    user = repositories.get_user_by_username(session, username)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def log_action(session: Session, user_id: int | None, action: str, details: str | None = None) -> AuditLog:
    audit = AuditLog(user_id=user_id, action=action, details=details)
    return repositories.create_audit(session, audit)


def register_client(session: Session, full_name: str, document_id: str, phone: str | None) -> Client:
    client = Client(full_name=full_name, document_id=document_id, phone=phone)
    return repositories.create_client(session, client)
