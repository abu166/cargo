from datetime import datetime
from pydantic import BaseModel
from shared.shipment_status import ShipmentStatus


class ShipmentCreate(BaseModel):
    client_id: int | None = None
    origin_station: str
    destination_station: str
    weight_kg: float | None = None
    length_cm: float | None = None
    width_cm: float | None = None
    height_cm: float | None = None


class ShipmentOut(BaseModel):
    id: int
    shipment_id: str
    client_id: int | None
    origin_station: str
    destination_station: str
    weight_kg: float | None
    length_cm: float | None
    width_cm: float | None
    height_cm: float | None
    status: ShipmentStatus
    created_at: datetime


class StatusUpdate(BaseModel):
    status: ShipmentStatus


class QRResponse(BaseModel):
    id: int
    qr_base64: str
    created_at: datetime


class DocumentGenerate(BaseModel):
    shipment_id: int
    doc_types: list[str]


class DocumentOut(BaseModel):
    id: int
    shipment_id: int
    doc_type: str
    content: str
    created_at: datetime


class ScanCreate(BaseModel):
    shipment_id: int
    scanned_by: str
    location: str


class ScanOut(BaseModel):
    id: int
    shipment_id: int
    scanned_by: str
    location: str
    created_at: datetime


class DropoffConfirm(BaseModel):
    weight_kg: float
    length_cm: float | None = None
    width_cm: float | None = None
    height_cm: float | None = None
