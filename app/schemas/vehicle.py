"""Pydantic schemas for vehicle profiles."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

from app.core.reference import COUNTRY_CODES, normalise_country, normalise_latin_text
from app.core.vehicle_catalog import load_catalog
from app.models.vehicle import BodyType, CargoShape, VehicleType

CURRENT_YEAR = datetime.now(UTC).year

Payload = Annotated[int, Field(gt=0, le=60_000, description="Maximum payload in kg")]
Volume = Annotated[float | None, Field(default=None, gt=0, le=300)]
RangeKm = Annotated[int | None, Field(default=None, gt=0, le=5_000)]
Dimension = Annotated[float | None, Field(default=None, gt=0, le=40, description="Metres")]
ModelYear = Annotated[int, Field(ge=1980, le=CURRENT_YEAR + 1, description="First registration")]
Plate = Annotated[str, Field(min_length=3, max_length=20, description="Registration plate")]
Make = Annotated[str, Field(min_length=1, max_length=40, description="Catalogue make code")]
Model = Annotated[str, Field(min_length=1, max_length=40, description="Catalogue model code")]
Modification = Annotated[str | None, Field(default=None, max_length=40)]
Vin = Annotated[
    str | None,
    Field(default=None, min_length=17, max_length=17, description="17 characters, no I/O/Q"),
]
CountryCode = Annotated[str, Field(min_length=2, max_length=2)]


def normalise_vin(value: str | None) -> str | None:
    """Upper-case a VIN and reject what ISO 3779 excludes; empty means "not provided"."""
    if value is None or not value.strip():
        return None
    cleaned = value.strip().upper()
    # ISO 3779 leaves out I, O and Q to avoid confusion with digits. The check digit is not
    # verified: it is optional in Europe, and rejecting a valid German or Polish VIN would be worse
    # than skipping a typo check.
    if not cleaned.isalnum() or any(char in "IOQ" for char in cleaned):
        raise ValueError("VIN may contain letters and digits, but not I, O or Q")
    return cleaned


class VehicleBase(BaseModel):
    make: Make
    model: Model
    modification: Modification = None
    model_year: ModelYear
    vin: Vin = None
    plate: Plate
    registration_country: CountryCode

    vehicle_type: VehicleType
    body_type: BodyType = BodyType.box
    payload_kg: Payload
    volume_m3: Volume = None
    max_range_km: RangeKm = None

    cargo_shape: CargoShape = CargoShape.box
    cargo_length_m: Dimension = None
    cargo_width_m: Dimension = None
    cargo_height_m: Dimension = None

    @field_validator("make", "model")
    @classmethod
    def _normalise_code(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("modification")
    @classmethod
    def _clean_modification(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return normalise_latin_text(value, field="modification")

    @field_validator("plate")
    @classmethod
    def _clean_plate(cls, value: str) -> str:
        return normalise_latin_text(value, field="plate").upper()

    @field_validator("registration_country")
    @classmethod
    def _clean_country(cls, value: str) -> str:
        return normalise_country(value, COUNTRY_CODES)

    @field_validator("vin")
    @classmethod
    def _clean_vin(cls, value: str | None) -> str | None:
        return normalise_vin(value)


class VehicleCreate(VehicleBase):
    @model_validator(mode="after")
    def _catalog_must_know_the_vehicle(self) -> VehicleCreate:
        # The pickers only offer catalogue entries, so this is the guard against a stale client or
        # a hand-written request, not the normal path.
        catalog = load_catalog()
        if catalog.make(self.make) is None:
            raise ValueError(f"unknown make {self.make!r}")
        if not catalog.has_model(self.make, self.model):
            raise ValueError(f"unknown model {self.model!r} for make {self.make!r}")
        return self


class VehicleUpdate(BaseModel):
    """Partial update: only the fields present in the request are touched."""

    make: Annotated[str | None, Field(default=None, min_length=1, max_length=40)] = None
    model: Annotated[str | None, Field(default=None, min_length=1, max_length=40)] = None
    modification: Annotated[str | None, Field(default=None, max_length=40)] = None
    model_year: Annotated[int | None, Field(default=None, ge=1980, le=CURRENT_YEAR + 1)] = None
    vin: Annotated[str | None, Field(default=None, min_length=17, max_length=17)] = None
    plate: Annotated[str | None, Field(default=None, min_length=3, max_length=20)] = None
    registration_country: Annotated[str | None, Field(default=None, min_length=2, max_length=2)] = (
        None
    )

    vehicle_type: VehicleType | None = None
    body_type: BodyType | None = None
    payload_kg: Annotated[int | None, Field(default=None, gt=0, le=60_000)] = None
    volume_m3: Annotated[float | None, Field(default=None, gt=0, le=300)] = None
    max_range_km: Annotated[int | None, Field(default=None, gt=0, le=5_000)] = None

    cargo_shape: CargoShape | None = None
    cargo_length_m: Annotated[float | None, Field(default=None, gt=0, le=40)] = None
    cargo_width_m: Annotated[float | None, Field(default=None, gt=0, le=40)] = None
    cargo_height_m: Annotated[float | None, Field(default=None, gt=0, le=40)] = None

    @field_validator("make", "model")
    @classmethod
    def _normalise_code(cls, value: str | None) -> str | None:
        return None if value is None else value.strip().lower()

    @field_validator("modification")
    @classmethod
    def _clean_modification(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return normalise_latin_text(value, field="modification")

    @field_validator("plate")
    @classmethod
    def _clean_plate(cls, value: str | None) -> str | None:
        return None if value is None else normalise_latin_text(value, field="plate").upper()

    @field_validator("registration_country")
    @classmethod
    def _clean_country(cls, value: str | None) -> str | None:
        return None if value is None else normalise_country(value, COUNTRY_CODES)

    @field_validator("vin")
    @classmethod
    def _clean_vin(cls, value: str | None) -> str | None:
        return normalise_vin(value)


class VehicleRead(VehicleBase):
    """A stored vehicle plus the human names behind its catalogue codes."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def make_name(self) -> str:
        make = load_catalog().make(self.make)
        return make.name if make else self.make.upper()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def model_name(self) -> str:
        return load_catalog().model_name(self.make, self.model) or self.model.upper()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def display_name(self) -> str:
        """`MAN TGX 18.440, 2021` — what the fleet list and dialogs show."""
        parts = [self.make_name, self.model_name]
        if self.modification:
            parts.append(self.modification)
        return f"{' '.join(parts)}, {self.model_year}"


class VehicleList(BaseModel):
    items: list[VehicleRead]
    total: int
