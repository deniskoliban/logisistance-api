"""Static reference data: the European countries a carrier can register from, and the text rules."""

from __future__ import annotations

import unicodedata

# EU member states.
EU_COUNTRY_CODES: tuple[str, ...] = (
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE",
)

# EEA + Switzerland: common for EU road freight operations.
EEA_EXTRA_COUNTRY_CODES: tuple[str, ...] = ("IS", "LI", "NO", "CH")

COUNTRY_CODES: tuple[str, ...] = EU_COUNTRY_CODES + EEA_EXTRA_COUNTRY_CODES

_COUNTRY_NAMES: dict[str, str] = {
    "AT": "Austria", "BE": "Belgium", "BG": "Bulgaria", "HR": "Croatia", "CY": "Cyprus",
    "CZ": "Czechia", "DK": "Denmark", "EE": "Estonia", "FI": "Finland", "FR": "France",
    "DE": "Germany", "GR": "Greece", "HU": "Hungary", "IE": "Ireland", "IT": "Italy",
    "LV": "Latvia", "LT": "Lithuania", "LU": "Luxembourg", "MT": "Malta",
    "NL": "Netherlands", "PL": "Poland", "PT": "Portugal", "RO": "Romania",
    "SK": "Slovakia", "SI": "Slovenia", "ES": "Spain", "SE": "Sweden",
    "IS": "Iceland", "LI": "Liechtenstein", "NO": "Norway", "CH": "Switzerland",
}


def country_name(code: str) -> str:
    return _COUNTRY_NAMES.get(code, code)


def normalise_country(value: str, allowed: tuple[str, ...]) -> str:
    """Uppercase, trim, and check a two-letter country code against the allowed set."""
    code = value.strip().upper()
    if code not in allowed:
        raise ValueError(f"unsupported country code {value!r}; expected one of: {', '.join(allowed)}")
    return code


def normalise_whitespace(value: str) -> str:
    """Collapse runs of whitespace and trim the ends."""
    return " ".join(value.split())


# Stored data keeps one format no matter the UI language (`CONVENTIONS.md` § Data format): Latin
# script, ASCII digits and the punctuation real names and plates use. The web client applies the
# same rule before submitting; this one is the authority.
_ALLOWED_PUNCTUATION = frozenset(" .,'’&/()#+-")


def is_latin_text(value: str) -> bool:
    """Whether `value` stays inside the Latin-only data format."""
    for char in value:
        if char in _ALLOWED_PUNCTUATION or (char.isascii() and char.isalnum()):
            continue
        if unicodedata.combining(char):
            continue
        if not unicodedata.name(char, "").startswith("LATIN "):
            return False
    return True


def normalise_latin_text(value: str, *, field: str) -> str:
    """Trimmed text, rejected when it leaves the Latin-only format."""
    cleaned = normalise_whitespace(value)
    if not is_latin_text(cleaned):
        raise ValueError(f"{field} must use Latin characters only")
    return cleaned
