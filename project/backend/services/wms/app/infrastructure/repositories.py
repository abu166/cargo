from sqlalchemy.orm import Session

from app.domain.models import Warehouse, StorageCell, CellSession, SensorReading, WMSEvent, RoutePlan, Measurement


def list_warehouses(session: Session) -> list[Warehouse]:
    return session.query(Warehouse).all()


def list_cells(session: Session, status: str | None = None) -> list[StorageCell]:
    query = session.query(StorageCell)
    if status:
        query = query.filter(StorageCell.status == status)
    return query.all()


def get_cell(session: Session, cell_id: int) -> StorageCell | None:
    return session.query(StorageCell).get(cell_id)


def create_session(session: Session, cell_session: CellSession) -> CellSession:
    session.add(cell_session)
    session.commit()
    session.refresh(cell_session)
    return cell_session


def get_session(session: Session, session_id: int) -> CellSession | None:
    return session.query(CellSession).get(session_id)


def update_cell(session: Session, cell: StorageCell) -> StorageCell:
    session.commit()
    session.refresh(cell)
    return cell


def create_event(session: Session, event: WMSEvent) -> WMSEvent:
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def create_measurement(session: Session, measurement: Measurement) -> Measurement:
    session.add(measurement)
    session.commit()
    session.refresh(measurement)
    return measurement


def create_route_plan(session: Session, plan: RoutePlan) -> RoutePlan:
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan


def get_route_plan(session: Session, plan_id: int) -> RoutePlan | None:
    return session.query(RoutePlan).get(plan_id)
