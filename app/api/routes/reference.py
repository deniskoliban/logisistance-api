"""Reference data for the UI (country pickers, enum labels)."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.reference import COUNTRY_CODES, country_name
from app.models.vehicle import BodyType, VehicleType
from app.schemas.reference import CountryOption, OptionItem, ReferenceData

router = APIRouter(prefix="/reference", tags=["reference"])


@router.get("/countries", response_model=list[CountryOption])
def list_countries() -> list[CountryOption]:
    return [
        CountryOption(code=code, name=country_name(code))
        for code in sorted(COUNTRY_CODES, key=country_name)
    ]


@router.get("/vehicle-options", response_model=ReferenceData)
def list_vehicle_options() -> ReferenceData:
    return ReferenceData(
        vehicle_types=[OptionItem(value=t.value, label=_humanise(t.value)) for t in VehicleType],
        body_types=[OptionItem(value=b.value, label=_humanise(b.value)) for b in BodyType],
    )


def _humanise(value: str) -> str:
    return value.replace("_", " ").capitalize()
