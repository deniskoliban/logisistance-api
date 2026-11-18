"""Reference data for the UI (country pickers, the vehicle catalogue, enum labels)."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.reference import COUNTRY_CODES, country_name
from app.core.vehicle_catalog import load_catalog
from app.models.vehicle import BodyType, CargoShape, VehicleType
from app.schemas.reference import (
    CountryOption,
    OptionItem,
    ReferenceData,
    VehicleCatalogResponse,
    VehicleMakeOption,
    VehicleModelOption,
)

router = APIRouter(prefix="/reference", tags=["reference"])


@router.get("/countries", response_model=list[CountryOption])
def list_countries() -> list[CountryOption]:
    return [
        CountryOption(code=code, name=country_name(code))
        for code in sorted(COUNTRY_CODES, key=country_name)
    ]


@router.get("/vehicle-catalog", response_model=VehicleCatalogResponse)
def vehicle_catalog() -> VehicleCatalogResponse:
    """Every make and model the pickers offer, curated makes first.

    Served whole: a few dozen kilobytes gzipped, cached by the client service, and it keeps the
    form usable offline once loaded — a carrier in a truck has no reliable connection.
    """
    catalog = load_catalog()
    return VehicleCatalogResponse(
        source=catalog.source,
        makes=[
            VehicleMakeOption(
                code=make.code,
                name=make.name,
                core=make.core,
                kinds=list(make.kinds),
                models=[VehicleModelOption(code=m.code, name=m.name) for m in make.models],
            )
            for make in catalog.makes
        ],
    )


@router.get("/vehicle-options", response_model=ReferenceData)
def list_vehicle_options() -> ReferenceData:
    return ReferenceData(
        vehicle_types=[OptionItem(value=t.value, label=_humanise(t.value)) for t in VehicleType],
        body_types=[OptionItem(value=b.value, label=_humanise(b.value)) for b in BodyType],
        cargo_shapes=[OptionItem(value=s.value, label=_humanise(s.value)) for s in CargoShape],
    )


def _humanise(value: str) -> str:
    return value.replace("_", " ").capitalize()
