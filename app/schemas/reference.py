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
