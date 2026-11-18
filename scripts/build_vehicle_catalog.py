"""Build the vehicle make/model catalogue shipped with the API.

Run by hand, not at runtime:

    .\\.venv\\Scripts\\python.exe scripts\\build_vehicle_catalog.py

Source: VehiclesDB (CC BY 4.0, https://vehiclesdb.com), a dataset assembled from official EU
vehicle registers. Two layers are produced:

* **core** makes (~22 that an EU road-freight carrier actually runs) with hand-curated *model
  families*: the registers list every variant as its own "model" — Scania alone has 214 entries
  (`R450`, `R460`, `R580LA6X2`, `92H`, …) — so the curated layer folds them into nameplates
  (`R`, `S`, `P`) and leaves the designation (`R450`) to the free-text modification field.
* **every other make** from the dataset, with its models kept as the registers spell them, so a
  driver of an unusual or legacy vehicle can still register it.

Attribution is required by the licence: the header of the generated file, the app footer and
`docs/` all carry the "Vehicle data by VehiclesDB" notice.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path
from typing import Any

DATASET = "https://cdn.jsdelivr.net/gh/vehiclesdb/vehiclesdb@latest"
KINDS = ("truck", "van")
MODELS_PER_NON_CORE_MAKE = 40

OUTPUT = Path(__file__).resolve().parent.parent / "app" / "core" / "data" / "vehicle_catalog.json"

# Curated core: dataset make slug -> (display name, model families in display order).
# A family name is what a carrier says out loud; the exact designation stays free text.
CORE: dict[str, tuple[str, list[str]]] = {
    "man": ("MAN", ["TGX", "TGS", "TGL", "TGM", "TGE", "TGA", "F2000", "M2000", "L2000"]),
    "daf": ("DAF", ["XG", "XF", "XD", "XB", "CF", "LF", "95", "85"]),
    "scania": ("Scania", ["S", "R", "G", "P", "L", "T", "4-Series", "3-Series"]),
    "volvo": ("Volvo", ["FH", "FH16", "FM", "FMX", "FE", "FL", "F10", "F12", "F16", "FL10"]),
    "mercedes-benz": (
        "Mercedes-Benz",
        [
            "Actros",
            "Arocs",
            "Atego",
            "Antos",
            "Axor",
            "Econic",
            "SK",
            "Sprinter",
            "Vito",
            "Citan",
            "Unimog",
        ],
    ),
    "iveco": (
        "Iveco",
        [
            "S-Way",
            "X-Way",
            "T-Way",
            "Stralis",
            "Eurocargo",
            "Eurotech",
            "Eurotrakker",
            "Trakker",
            "Daily",
        ],
    ),
    "renault": (
        "Renault Trucks",
        ["T", "C", "K", "Master", "Trafic", "Kangoo", "Magnum", "Premium", "Midlum", "Kerax"],
    ),
    "isuzu": ("Isuzu", ["D-Max", "N-Series", "F-Series", "Grafter", "Forward"]),
    "mitsubishi-fuso": ("Mitsubishi Fuso", ["Canter", "eCanter", "FE", "FV"]),
    "sisu": ("Sisu", ["Polar", "R-Series", "C-Series"]),
    "tatra": ("Tatra", ["Phoenix", "Force", "T815"]),
    "volkswagen": (
        "Volkswagen",
        ["Crafter", "Transporter", "Caddy", "Amarok", "ID. Buzz Cargo"],
    ),
    "ford": (
        "Ford",
        ["Transit", "Transit Custom", "Transit Connect", "Transit Courier", "Ranger", "F-Max"],
    ),
    "fiat": ("Fiat", ["Ducato", "Doblò", "Fiorino", "Scudo"]),
    "peugeot": ("Peugeot", ["Boxer", "Expert", "Partner", "Bipper"]),
    "citroen": ("Citroën", ["Jumper", "Jumpy", "Berlingo", "Nemo"]),
    "opel": ("Opel", ["Movano", "Vivaro", "Combo"]),
    "nissan": ("Nissan", ["Interstar", "Primastar", "NV400", "NV300", "Townstar"]),
    "toyota": ("Toyota", ["Proace", "Proace City", "Hilux"]),
    "maxus": ("Maxus", ["Deliver 7", "Deliver 9", "eDeliver 3", "eDeliver 9", "T60", "T90"]),
    "byd": ("BYD", ["E-Vali", "ETP3", "T3"]),
    "volta-trucks": ("Volta Trucks", ["Zero"]),
}

_DIGITS_ONLY = re.compile(r"^\d{1,4}$")


def slugify(value: str) -> str:
    """Stable, URL-safe code for a curated family name (`Doblò` -> `doblo`, `ID. Buzz Cargo` -> `id-buzz-cargo`)."""
    # Decompose first: otherwise `Doblò` loses the accented letter instead of transliterating it.
    ascii_value = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(char for char in ascii_value if not unicodedata.combining(char))
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    return slug or "model"


def fetch(path: str) -> Any:
    with urllib.request.urlopen(f"{DATASET}/{path}", timeout=60) as response:  # noqa: S310
        return json.load(response)


def main() -> int:
    makes: dict[str, dict[str, Any]] = {}
    models: dict[str, list[dict[str, Any]]] = {}

    for kind in KINDS:
        for make in fetch(f"catalog/{kind}/makes.json"):
            entry = makes.setdefault(
                make["slug"], {"code": make["slug"], "name": make["name"], "kinds": []}
            )
            if kind not in entry["kinds"]:
                entry["kinds"].append(kind)
        for model in fetch(f"catalog/{kind}/models.json"):
            models.setdefault(model["make_id"], []).append(model)

    catalogue: list[dict[str, Any]] = []

    for code, (name, families) in CORE.items():
        if code not in makes:
            print(f"warning: curated make {code!r} is no longer in the dataset", file=sys.stderr)
            continue
        catalogue.append(
            {
                "code": code,
                "name": name,
                "core": True,
                "kinds": sorted(makes[code]["kinds"]),
                "models": [{"code": slugify(f), "name": f} for f in families],
            }
        )

    for code, make in sorted(makes.items(), key=lambda item: item[1]["name"].casefold()):
        if code in CORE:
            continue
        names = sorted(
            {
                model["name"].strip()
                for model in models.get(code, [])
                if model["name"].strip() and not _DIGITS_ONLY.match(model["name"].strip())
            },
            key=str.casefold,
        )[:MODELS_PER_NON_CORE_MAKE]
        catalogue.append(
            {
                "code": code,
                "name": make["name"],
                "core": False,
                "kinds": sorted(make["kinds"]),
                "models": [{"code": slugify(n), "name": n} for n in names],
            }
        )

    payload = {
        "_source": (
            "Vehicle data by VehiclesDB (https://vehiclesdb.com), CC BY 4.0, "
            "curated model families for core makes. Regenerate with scripts/build_vehicle_catalog.py"
        ),
        "makes": catalogue,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    total_models = sum(len(make["models"]) for make in catalogue)
    print(f"{len(catalogue)} makes, {total_models} models -> {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
