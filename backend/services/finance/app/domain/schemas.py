from datetime import datetime
from pydantic import BaseModel


class TariffCreate(BaseModel):
    name: str
    base_rate: float
    per_kg_rate: float


class TariffOut(BaseModel):
    id: int
    name: str
    base_rate: float
    per_kg_rate: float
    created_at: datetime


class TariffCalc(BaseModel):
    tariff_id: int
    weight_kg: float


class TariffCalcOut(BaseModel):
    tariff_id: int
    amount: float


class PaymentCreate(BaseModel):
    shipment_id: int
    amount: float
    method: str = "CASH"


class PaymentUpdate(BaseModel):
    status: str


class PaymentOut(BaseModel):
    id: int
    shipment_id: int
    amount: float
    status: str
    method: str
    created_at: datetime


class FO3Report(BaseModel):
    total_amount: float
    payments_count: int
