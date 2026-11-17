from __future__ import annotations

from enum import Enum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class VehicleType(str, Enum):
    van = "van"
    rigid_truck = "rigid_truck"
    articulated_truck = "articulated_truck"
    tractor_unit = "tractor_unit"
    trailer = "trailer"


class BodyType(str, Enum):
    box = "box"
    curtain_side = "curtain_side"
    refrigerated = "refrigerated"
    flatbed = "flatbed"
    tipper = "tipper"
    tanker = "tanker"
    other = "other"


class Vehicle(TimestampMixin, Base):
    """Basic commercial vehicle profile.

    Payload, volume and dimensions are what the freight search will later use to
    decide whether a load actually fits this vehicle.
    """

    __tablename__ = "vehicles"
    __table_args__ = (UniqueConstraint("owner_id", "plate", name="uq_vehicles_owner_plate"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    label: Mapped[str] = mapped_column(nullable=False)
    plate: Mapped[str] = mapped_column(index=True, nullable=False)
    vehicle_type: Mapped[VehicleType] = mapped_column(
        SAEnum(VehicleType, native_enum=False, length=32, validate_strings=True), nullable=False
    )
    body_type: Mapped[BodyType] = mapped_column(
        SAEnum(BodyType, native_enum=False, length=32, validate_strings=True),
        nullable=False,
        default=BodyType.box,
    )

    payload_kg: Mapped[int] = mapped_column(nullable=False)
    volume_m3: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    max_range_km: Mapped[int | None] = mapped_column(nullable=True)

    # Overall vehicle dimensions, metres.
    length_m: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    width_m: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    height_m: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Interior cargo compartment dimensions, metres.
    cargo_length_m: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    cargo_width_m: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    cargo_height_m: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    owner: Mapped["User"] = relationship(back_populates="vehicles")  # noqa: F821

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<Vehicle id={self.id} plate={self.plate!r} owner_id={self.owner_id}>"
