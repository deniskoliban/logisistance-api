"""Pydantic schemas for vehicle profiles."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.reference import normalise_whitespace
from app.models.vehicle import BodyType, VehicleType

Payload = Annotated[int, Field(gt=0, le=60_000, description="Maximum payload in kg")]
Volume = Annotated[float | None, Field(default=None, gt=0, le=300)]
RangeKm = Annotated[int | None, Field(default=None, gt=0, le=5_000)]
Dimension = Annotated[float | None, Field(default=None, gt=0, le=40, description="Metres")]


class VehicleBase(BaseModel):
    label: Annotated[str, Field(min_length=1, max_length=80, description="e.g. 'MAN TGX'")]
    plate: Annotated[str, Field(min_length=3, max_length=20, description="Registration plate")]
    vehicle_type: VehicleType
    body_type: BodyType = BodyType.box
    payload_kg: Payload
    volume_m3: Volume = None
    max_range_km: RangeKm = None

    length_m: Dimension = None
    width_m: Dimension = None
    height_m: Dimension = None

    cargo_length_m: Dimension = None
    cargo_width_m: Dimension = None
    cargo_height_m: Dimension = None

    @field_validator("label", "plate")
    @classmethod
    def _clean_text(cls, value: str) -> str:
        cleaned = normalise_whitespace(value)
        if len(cleaned) < 1:
            raise ValueError("must not be blank")
        return cleaned.upper() if len(cleaned) > 2 and cleaned.isalpha() else cleaned


class VehicleCreate(VehicleBase):
    @field_validator("plate")
    @classmethod
    def _normalise_plate(cls, value: str) -> str:
        return normalise_whitespace(value).upper()


class VehicleUpdate(BaseModel):
    label: Annotated[str | None, Field(default=None, min_length=1, max_length=80)] = None
    plate: Annotated[str | None, Field(default=None, min_length=3, max_length=20)] = None
    vehicle_type: VehicleType | None = None
    body_type: BodyType | None = None
    payload_kg: Annotated[int | None, Field(default=None, gt=0, le=60_000)] = None
    volume_m3: Annotated[float | None, Field(default=None, gt=0, le=300)] = None
    max_range_km: Annotated[int | None, Field(default=None, gt=0, le=5_000)] = None
    length_m: Annotated[float | None, Field(default=None, gt=0, le=40)] = None
    width_m: Annotated[float | None, Field(default=None, gt=0, le=40)] = None
    height_m: Annotated[float | None, Field(default=None, gt=0, le=40)] = None
    cargo_length_m: Annotated[float | None, Field(default=None, gt=0, le=40)] = None
    cargo_width_m: Annotated[float | None, Field(default=None, gt=0, le=40)] = None
    cargo_height_m: Annotated[float | None, Field(default=None, gt=0, le=40)] = None

    @field_validator("label", "plate")
    @classmethod
    def _clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = normalise_whitespace(value)
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned

    @field_validator("plate")
    @classmethod
    def _normalise_plate(cls, value: str | None) -> str | None:
        return None if value is None else value.upper()


class VehicleRead(VehicleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime


class VehicleList(BaseModel):
    items: list[VehicleRead]
    total: int
