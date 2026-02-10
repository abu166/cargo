from sqlalchemy.orm import Session

from app.domain.models import User, Client, AuditLog


def create_user(session: Session, user: User) -> User:
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_user_by_username(session: Session, username: str) -> User | None:
    return session.query(User).filter(User.username == username).first()


def list_users(session: Session) -> list[User]:
    return session.query(User).all()


def get_user(session: Session, user_id: int) -> User | None:
    return session.query(User).get(user_id)


def delete_user(session: Session, user: User) -> None:
    session.delete(user)
    session.commit()


def create_client(session: Session, client: Client) -> Client:
    session.add(client)
    session.commit()
    session.refresh(client)
    return client


def list_clients(session: Session) -> list[Client]:
    return session.query(Client).all()


def create_audit(session: Session, audit: AuditLog) -> AuditLog:
    session.add(audit)
    session.commit()
    session.refresh(audit)
    return audit


def list_audit(session: Session, limit: int = 200) -> list[AuditLog]:
    return session.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
