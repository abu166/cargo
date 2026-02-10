from sqlalchemy import String, DateTime, Float, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    client_id: Mapped[str] = mapped_column(String, nullable=False)
    client_name: Mapped[str | None] = mapped_column(String, nullable=True)
    client_email: Mapped[str | None] = mapped_column(String, nullable=True)
    from_station: Mapped[str] = mapped_column(String, nullable=False)
    to_station: Mapped[str] = mapped_column(String, nullable=False)
    current_station: Mapped[str | None] = mapped_column(String, nullable=True)
    next_station: Mapped[str | None] = mapped_column(String, nullable=True)
    route: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="В пути")
    departure_date: Mapped[str | None] = mapped_column(String, nullable=True)
    weight: Mapped[str | None] = mapped_column(String, nullable=True)
    dimensions: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    value: Mapped[str | None] = mapped_column(String, nullable=True)
    cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
