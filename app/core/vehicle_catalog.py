"""The vehicle make/model catalogue: what the pickers in the app offer.

The catalogue is a generated data file (`app/core/data/vehicle_catalog.json`, built by
`scripts/build_vehicle_catalog.py` from the open VehiclesDB dataset, CC BY 4.0) plus this small
lookup layer. Vehicles store the catalogue *codes*, and validation here is what keeps a vehicle
from pointing at a make or a model that does not exist.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_DATA_FILE = Path(__file__).resolve().parent / "data" / "vehicle_catalog.json"


@dataclass(frozen=True)
class CatalogModel:
    code: str
    name: str


@dataclass(frozen=True)
class CatalogMake:
    code: str
    name: str
    core: bool
    kinds: tuple[str, ...]
    models: tuple[CatalogModel, ...]


@dataclass(frozen=True)
class Catalog:
    source: str
    makes: tuple[CatalogMake, ...]

    def make(self, code: str) -> CatalogMake | None:
        """Look up a make by code, case-insensitively (the client may send `MAN`)."""
        wanted = code.strip().lower()
        return next((make for make in self.makes if make.code == wanted), None)

    def has_model(self, make_code: str, model_code: str) -> bool:
        make = self.make(make_code)
        if make is None:
            return False
        wanted = model_code.strip().lower()
        return any(model.code == wanted for model in make.models)

    def model_name(self, make_code: str, model_code: str) -> str | None:
        make = self.make(make_code)
        if make is None:
            return None
        wanted = model_code.strip().lower()
        return next((model.name for model in make.models if model.code == wanted), None)


@lru_cache(maxsize=1)
def load_catalog() -> Catalog:
    """Read and cache the generated catalogue (a few hundred kilobytes, once per process)."""
    payload = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
    makes = tuple(
        CatalogMake(
            code=entry["code"],
            name=entry["name"],
            core=bool(entry.get("core")),
            kinds=tuple(entry.get("kinds", ())),
            models=tuple(CatalogModel(code=m["code"], name=m["name"]) for m in entry["models"]),
        )
        for entry in payload["makes"]
    )
    return Catalog(source=payload.get("_source", ""), makes=makes)
