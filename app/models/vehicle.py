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


class CargoShape(str, Enum):
    """Whether the cargo bay is a rectangular box or has arches/slopes eating into it."""

    box = "box"
    irregular = "irregular"


class Vehicle(TimestampMixin, Base):
    """A real commercial vehicle: identified by make/model/year/VIN, sized for freight matching.

    Payload, usable volume and cargo-compartment dimensions are what the freight search will later
    use to decide whether a load actually fits. Overall vehicle dimensions are deliberately not
    stored: they never decide fit, and they change nothing for a load.
    """

    __tablename__ = "vehicles"
    __table_args__ = (
        UniqueConstraint("owner_id", "plate", name="uq_vehicles_owner_plate"),
        # The same truck added twice is a data error, not a second vehicle. NULLs stay distinct in
        # SQLite, so vehicles without a VIN do not collide.
        UniqueConstraint("owner_id", "vin", name="uq_vehicles_owner_vin"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # Identity: codes from the vehicle catalogue (`app/core/vehicle_catalog.py`).
    make: Mapped[str] = mapped_column(index=True, nullable=False)
    model: Mapped[str] = mapped_column(nullable=False)
    modification: Mapped[str | None] = mapped_column(nullable=True)
    model_year: Mapped[int] = mapped_column(nullable=False)
    vin: Mapped[str | None] = mapped_column(nullable=True)
    plate: Mapped[str] = mapped_column(index=True, nullable=False)
    registration_country: Mapped[str] = mapped_column(nullable=False)

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

    cargo_shape: Mapped[CargoShape] = mapped_column(
        SAEnum(CargoShape, native_enum=False, length=16, validate_strings=True),
        nullable=False,
        default=CargoShape.box,
    )
    # Interior cargo compartment dimensions, metres — maximums across the bay.
    cargo_length_m: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    cargo_width_m: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    cargo_height_m: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    owner: Mapped["User"] = relationship(back_populates="vehicles")  # noqa: F821

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return (
            f"<Vehicle id={self.id} make={self.make!r} model={self.model!r} "
            f"plate={self.plate!r} owner_id={self.owner_id}>"
        )
