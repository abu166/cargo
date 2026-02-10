from sqlalchemy.orm import Session

from app.domain.models import Tariff, Payment


def create_tariff(session: Session, tariff: Tariff) -> Tariff:
    session.add(tariff)
    session.commit()
    session.refresh(tariff)
    return tariff


def list_tariffs(session: Session) -> list[Tariff]:
    return session.query(Tariff).all()


def get_tariff(session: Session, tariff_id: int) -> Tariff | None:
    return session.query(Tariff).get(tariff_id)


def create_payment(session: Session, payment: Payment) -> Payment:
    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment


def list_payments(session: Session) -> list[Payment]:
    return session.query(Payment).all()


def get_payment(session: Session, payment_id: int) -> Payment | None:
    return session.query(Payment).get(payment_id)
