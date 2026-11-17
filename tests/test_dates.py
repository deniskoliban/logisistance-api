"""Driver-age rules derived from a date of birth."""

from __future__ import annotations

from datetime import date

import pytest

from app.core.dates import validate_driver_birth_date, years_since


def test_years_since_counts_completed_years_only() -> None:
    today = date(2026, 11, 17)

    assert years_since(date(1985, 4, 12), today) == 41
    assert years_since(date(1985, 11, 17), today) == 41  # birthday today
    assert years_since(date(1985, 11, 18), today) == 40  # birthday tomorrow


def test_years_since_handles_leap_day_birth() -> None:
    assert years_since(date(2000, 2, 29), date(2026, 2, 28)) == 25
    assert years_since(date(2000, 2, 29), date(2026, 3, 1)) == 26


def test_validate_accepts_working_age() -> None:
    assert validate_driver_birth_date(date(1990, 1, 1), date(2026, 11, 17)) == date(1990, 1, 1)


def test_validate_rejects_underage() -> None:
    with pytest.raises(ValueError, match="at least 18"):
        validate_driver_birth_date(date(2010, 1, 1), date(2026, 11, 17))


def test_validate_rejects_future_date() -> None:
    with pytest.raises(ValueError, match="future"):
        validate_driver_birth_date(date(2030, 1, 1), date(2026, 11, 17))


def test_validate_rejects_implausibly_old_driver() -> None:
    with pytest.raises(ValueError, match="at most 100"):
        validate_driver_birth_date(date(1900, 1, 1), date(2026, 11, 17))
