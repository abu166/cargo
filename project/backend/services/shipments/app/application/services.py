import base64
import io
import secrets

import qrcode
from sqlalchemy.orm import Session

from app.domain.models import Shipment, QRCode, Document, ScanEvent
from app.infrastructure import repositories
from shared.shipment_status import ShipmentStatus


ALLOWED_TRANSITIONS = {
    ShipmentStatus.CREATED: {ShipmentStatus.DROPPED_OFF, ShipmentStatus.TARIFF_CALCULATED},
    ShipmentStatus.DROPPED_OFF: {ShipmentStatus.TARIFF_CALCULATED},
    ShipmentStatus.TARIFF_CALCULATED: {ShipmentStatus.PAID},
    ShipmentStatus.PAID: {ShipmentStatus.QR_GENERATED},
    ShipmentStatus.QR_GENERATED: {ShipmentStatus.DOCUMENTS_CREATED},
    ShipmentStatus.DOCUMENTS_CREATED: {ShipmentStatus.STORED_IN_CELL, ShipmentStatus.LOADED},
    ShipmentStatus.STORED_IN_CELL: {ShipmentStatus.LOADED},
    ShipmentStatus.LOADED: {ShipmentStatus.IN_TRANSIT},
    ShipmentStatus.IN_TRANSIT: {ShipmentStatus.ARRIVED},
    ShipmentStatus.ARRIVED: {ShipmentStatus.NOTIFIED},
    ShipmentStatus.NOTIFIED: {ShipmentStatus.ISSUED},
    ShipmentStatus.ISSUED: {ShipmentStatus.CLOSED},
}


def generate_shipment_code() -> str:
    return f"SHP-{secrets.token_hex(4).upper()}"


def create_shipment(session: Session, shipment: Shipment) -> Shipment:
    shipment.shipment_id = generate_shipment_code()
    shipment.status = ShipmentStatus.CREATED.value
    return repositories.create_shipment(session, shipment)


def update_status(session: Session, shipment: Shipment, new_status: ShipmentStatus) -> Shipment:
    current = ShipmentStatus(shipment.status)
    if new_status == current:
        return shipment
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if new_status not in allowed:
        raise ValueError(f"Transition {current} -> {new_status} not allowed")
    shipment.status = new_status.value
    session.commit()
    session.refresh(shipment)
    return shipment


def create_qr(session: Session, shipment: Shipment) -> QRCode:
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(shipment.shipment_id)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    qr_code = QRCode(shipment_id=shipment.id, qr_base64=encoded)
    return repositories.save_qr(session, qr_code)


def generate_documents(session: Session, shipment: Shipment, doc_types: list[str]) -> list[Document]:
    docs = []
    for doc_type in doc_types:
        content = f"Document {doc_type} for shipment {shipment.shipment_id}"
        doc = Document(shipment_id=shipment.id, doc_type=doc_type, content=content)
        docs.append(repositories.save_document(session, doc))
    return docs


def register_scan(session: Session, shipment: Shipment, scanned_by: str, location: str) -> ScanEvent:
    scan = ScanEvent(shipment_id=shipment.id, scanned_by=scanned_by, location=location)
    return repositories.create_scan_event(session, scan)
