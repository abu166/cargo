from datetime import datetime
from pydantic import BaseModel


class WarehouseOut(BaseModel):
    id: int
    name: str
    location: str
    created_at: datetime


class CellOut(BaseModel):
    id: int
    warehouse_id: int
    code: str
    status: str
    created_at: datetime


class SessionCreate(BaseModel):
    shipment_id: int | None = None


class SessionOut(BaseModel):
    id: int
    cell_id: int | None
    shipment_id: int | None
    status: str
    created_at: datetime
    opened_at: datetime | None
    closed_at: datetime | None


class EventCreate(BaseModel):
    session_id: int | None
    event_type: str
    payload: str | None = None


class EventOut(BaseModel):
    id: int
    session_id: int | None
    event_type: str
    payload: str | None
    created_at: datetime


class MeasurementCreate(BaseModel):
    shipment_id: int
    weight_kg: float
    length_cm: float | None = None
    width_cm: float | None = None
    height_cm: float | None = None
    discrepancy_flag: bool = False


class MeasurementOut(BaseModel):
    id: int
    shipment_id: int
    weight_kg: float
    length_cm: float | None
    width_cm: float | None
    height_cm: float | None
    discrepancy_flag: bool
    created_at: datetime


class RoutePlanCreate(BaseModel):
    origin_station: str
    destination_station: str
    wagons_count: int


class RoutePlanOut(BaseModel):
    id: int
    origin_station: str
    destination_station: str
    wagons_count: int
    status: str
    created_at: datetime


class TransportAction(BaseModel):
    shipment_id: int


class DeliveryAction(BaseModel):
    shipment_id: int


class ScanCreate(BaseModel):
    shipment_id: int
    scanned_by: str
    location: str
