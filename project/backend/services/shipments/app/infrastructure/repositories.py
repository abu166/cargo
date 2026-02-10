from sqlalchemy.orm import Session

from app.domain.models import Shipment, QRCode, Document, ScanEvent


def create_shipment(session: Session, shipment: Shipment) -> Shipment:
    session.add(shipment)
    session.commit()
    session.refresh(shipment)
    return shipment


def list_shipments(session: Session) -> list[Shipment]:
    return session.query(Shipment).all()


def get_shipment(session: Session, shipment_id: int) -> Shipment | None:
    return session.query(Shipment).get(shipment_id)


def get_shipment_by_code(session: Session, shipment_code: str) -> Shipment | None:
    return session.query(Shipment).filter(Shipment.shipment_id == shipment_code).first()


def save_qr(session: Session, qr: QRCode) -> QRCode:
    session.add(qr)
    session.commit()
    session.refresh(qr)
    return qr


def save_document(session: Session, doc: Document) -> Document:
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc


def get_document(session: Session, doc_id: int) -> Document | None:
    return session.query(Document).get(doc_id)


def create_scan_event(session: Session, scan: ScanEvent) -> ScanEvent:
    session.add(scan)
    session.commit()
    session.refresh(scan)
    return scan
