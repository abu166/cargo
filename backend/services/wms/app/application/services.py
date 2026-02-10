import httpx
from sqlalchemy.orm import Session

from app.domain.models import CellSession, WMSEvent, Measurement, RoutePlan
from app.infrastructure import repositories
from shared.shipment_status import ShipmentStatus


def create_cell_session(session: Session, shipment_id: int | None) -> CellSession:
    cell_session = CellSession(shipment_id=shipment_id)
    return repositories.create_session(session, cell_session)


def log_event(session: Session, session_id: int | None, event_type: str, payload: str | None) -> WMSEvent:
    event = WMSEvent(session_id=session_id, event_type=event_type, payload=payload)
    return repositories.create_event(session, event)


def record_measurement(session: Session, shipment_id: int, weight_kg: float, length_cm: float | None, width_cm: float | None, height_cm: float | None, discrepancy_flag: bool) -> Measurement:
    measurement = Measurement(
        shipment_id=shipment_id,
        weight_kg=weight_kg,
        length_cm=length_cm,
        width_cm=width_cm,
        height_cm=height_cm,
        discrepancy_flag=discrepancy_flag,
    )
    return repositories.create_measurement(session, measurement)


def create_route_plan(session: Session, origin: str, destination: str, wagons_count: int) -> RoutePlan:
    plan = RoutePlan(origin_station=origin, destination_station=destination, wagons_count=wagons_count)
    return repositories.create_route_plan(session, plan)


def approve_route_plan(session: Session, plan: RoutePlan) -> RoutePlan:
    plan.status = "APPROVED"
    session.commit()
    session.refresh(plan)
    return plan


def update_shipment_status(shipments_url: str, token: str, shipment_id: int, status: ShipmentStatus):
    with httpx.Client(timeout=5.0) as client:
        response = client.post(
            f"{shipments_url}/shipments/{shipment_id}/status",
            json={"status": status.value},
            headers={"Authorization": f"Bearer {token}"},
        )
    response.raise_for_status()
    return response.json()


def get_shipment(shipments_url: str, token: str, shipment_id: int):
    with httpx.Client(timeout=5.0) as client:
        response = client.get(
            f"{shipments_url}/shipments/{shipment_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
    response.raise_for_status()
    return response.json()


def advance_shipment_status(shipments_url: str, token: str, shipment_id: int, ordered: list[ShipmentStatus]):
    current = get_shipment(shipments_url, token, shipment_id).get("status")
    if current is None:
        return None
    order_values = [s.value for s in ordered]
    if current in order_values:
        start_index = order_values.index(current) + 1
    else:
        start_index = 0
    result = None
    for status in ordered[start_index:]:
        result = update_shipment_status(shipments_url, token, shipment_id, status)
    return result


def confirm_dropoff(shipments_url: str, token: str, shipment_id: int, weight_kg: float, length_cm: float | None, width_cm: float | None, height_cm: float | None):
    with httpx.Client(timeout=5.0) as client:
        response = client.post(
            f"{shipments_url}/shipments/{shipment_id}/dropoff/confirm",
            json={
                "weight_kg": weight_kg,
                "length_cm": length_cm,
                "width_cm": width_cm,
                "height_cm": height_cm,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    response.raise_for_status()
    return response.json()


def forward_scan(shipments_url: str, token: str, shipment_id: int, scanned_by: str, location: str):
    with httpx.Client(timeout=5.0) as client:
        response = client.post(
            f"{shipments_url}/scan",
            json={"shipment_id": shipment_id, "scanned_by": scanned_by, "location": location},
            headers={"Authorization": f"Bearer {token}"},
        )
    response.raise_for_status()
    return response.json()
