"""Date helpers for driver age rules."""

from __future__ import annotations

from datetime import date

MIN_DRIVER_AGE = 18
MAX_DRIVER_AGE = 100


def years_since(birth_date: date, today: date | None = None) -> int:
    """Whole years elapsed between birth_date and today (birthday-aware)."""
    today = today or date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def validate_driver_birth_date(value: date, today: date | None = None) -> date:
    """Raise ValueError unless the date of birth belongs to a plausible driver age."""
    today = today or date.today()
    if value > today:
        raise ValueError("date of birth cannot be in the future")

    age = years_since(value, today)
    if age < MIN_DRIVER_AGE:
        raise ValueError(f"drivers must be at least {MIN_DRIVER_AGE} years old")
    if age > MAX_DRIVER_AGE:
        raise ValueError(f"drivers must be at most {MAX_DRIVER_AGE} years old")
    return value
