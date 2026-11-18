"""One-off patch for scripts/build_vehicle_catalog.py: extend curated families and fix digit-only names."""

from __future__ import annotations

import ast
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "scripts" / "build_vehicle_catalog.py"
source = PATH.read_text(encoding="utf-8")


def block(indent: str, items: list[str]) -> str:
    """A Python list literal laid out one name per line at the given indentation."""
    lines = [f"{indent}["]
    lines += [f'{indent}    "{item}",' for item in items]
    lines.append(f"{indent}],")
    return "\n".join(lines)


RENAULT_OLD = (
    '        ["T", "C", "K", "Master", "Trafic", "Kangoo", "Magnum", "Premium", "Midlum", "Kerax"],'
)
RENAULT_NEW = block(
    "        ",
    [
        "T",
        "C",
        "K",
        "Master",
        "Trafic",
        "Kangoo",
        "Express",
        "Magnum",
        "Premium",
        "Midlum",
        "Kerax",
        "Maxity",
        "Mascott",
    ],
)

VW_OLD = '        ["Crafter", "Transporter", "Caddy", "Amarok", "ID. Buzz Cargo"],'
VW_NEW = '        ["Crafter", "Transporter", "Caddy", "Amarok", "ID. Buzz Cargo", "LT"],'

FORD_OLD = (
    '        ["Transit", "Transit Custom", "Transit Connect", "Transit Courier", "Ranger", "F-Max"],'
)
FORD_NEW = block(
    "        ",
    [
        "Transit",
        "Transit Custom",
        "Transit Connect",
        "Transit Courier",
        "Ranger",
        "F-Max",
        "Cargo",
    ],
)

DIGITS_OLD = """        names = sorted(
            {
                model["name"].strip()
                for model in models.get(code, [])
                if model["name"].strip() and not _DIGITS_ONLY.match(model["name"].strip())
            },
            key=str.casefold,
        )[:MODELS_PER_NON_CORE_MAKE]"""
DIGITS_NEW = """        all_names = sorted(
            {model["name"].strip() for model in models.get(code, []) if model["name"].strip()},
            key=str.casefold,
        )
        # Digit-only names are usually register noise ("415", "12"), but some makes have nothing else:
        # Zil 130, Ural 375 and Steyr 586 are real vehicles, and filtering them left 9 makes unusable.
        names = [name for name in all_names if not _DIGITS_ONLY.match(name)] or all_names
        names = names[:MODELS_PER_NON_CORE_MAKE]"""

replacements: list[tuple[str, str]] = [
    (RENAULT_OLD, RENAULT_NEW),
    (VW_OLD, VW_NEW),
    (FORD_OLD, FORD_NEW),
    (
        '            "Unimog",\n',
        '            "Unimog",\n            "Vario",\n            "Zetros",\n',
    ),
    ('            "Daily",\n', '            "Daily",\n            "Massif",\n            "Acco",\n'),
    (DIGITS_OLD, DIGITS_NEW),
]

for old, new in replacements:
    if old not in source:
        raise SystemExit(f"patch target missing:\n{old[:120]}")
    source = source.replace(old, new, 1)

PATH.write_text(source, encoding="utf-8")
ast.parse(source)
print("patched and syntax-checked")
