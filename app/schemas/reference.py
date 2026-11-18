"""Reference data response schemas."""

from __future__ import annotations

from pydantic import BaseModel


class CountryOption(BaseModel):
    code: str
    name: str


class OptionItem(BaseModel):
    value: str
    label: str


class ReferenceData(BaseModel):
    vehicle_types: list[OptionItem]
    body_types: list[OptionItem]
    cargo_shapes: list[OptionItem]


class VehicleModelOption(BaseModel):
    code: str
    name: str


class VehicleMakeOption(BaseModel):
    code: str
    name: str
    #: Curated makes come first in the picker: their models are nameplate families, not
    #: register noise (`app/core/vehicle_catalog.py`).
    core: bool
    kinds: list[str]
    models: list[VehicleModelOption]


class VehicleCatalogResponse(BaseModel):
    #: Licence notice for the generated dataset; the client shows it where the catalogue is used.
    source: str
    makes: list[VehicleMakeOption]
