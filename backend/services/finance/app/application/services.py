from sqlalchemy.orm import Session

from app.domain.models import Tariff, Payment
from app.infrastructure import repositories


def create_tariff(session: Session, name: str, base_rate: float, per_kg_rate: float) -> Tariff:
    tariff = Tariff(name=name, base_rate=base_rate, per_kg_rate=per_kg_rate)
    return repositories.create_tariff(session, tariff)


def calculate_amount(session: Session, tariff_id: int, weight_kg: float) -> float:
    tariff = repositories.get_tariff(session, tariff_id)
    if not tariff:
        raise ValueError("Tariff not found")
    return tariff.base_rate + tariff.per_kg_rate * weight_kg


def create_payment(session: Session, shipment_id: int, amount: float, method: str) -> Payment:
    payment = Payment(shipment_id=shipment_id, amount=amount, method=method)
    return repositories.create_payment(session, payment)


def update_payment_status(session: Session, payment: Payment, status: str) -> Payment:
    payment.status = status
    session.commit()
    session.refresh(payment)
    return payment
