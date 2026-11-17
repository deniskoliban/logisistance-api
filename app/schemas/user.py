"""Pydantic schemas for auth and user profile."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field, field_validator

from app.core.dates import validate_driver_birth_date, years_since
from app.core.reference import COUNTRY_CODES, normalise_country, normalise_whitespace

Name = Annotated[str, Field(min_length=2, max_length=120)]
BirthDate = Annotated[date, Field(description="Date of birth, ISO 8601 (YYYY-MM-DD)")]
City = Annotated[str, Field(min_length=2, max_length=120)]
Password = Annotated[str, Field(min_length=8, max_length=128)]


class UserRegister(BaseModel):
    email: EmailStr
    password: Password
    full_name: Name
    date_of_birth: BirthDate
    country: str = Field(
        min_length=2,
        max_length=2,
        description="Country of residence, also the default starting point for load search",
    )
    city: City

    @field_validator("full_name", "city")
    @classmethod
    def _clean_text(cls, value: str) -> str:
        cleaned = normalise_whitespace(value)
        if len(cleaned) < 2:
            raise ValueError("must contain at least 2 non-space characters")
        return cleaned

    @field_validator("country")
    @classmethod
    def _validate_country(cls, value: str) -> str:
        return normalise_country(value, allowed=COUNTRY_CODES)

    @field_validator("date_of_birth")
    @classmethod
    def _validate_date_of_birth(cls, value: date) -> date:
        return validate_driver_birth_date(value)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserUpdate(BaseModel):
    """Partial profile update. Unset fields are left untouched."""

    full_name: Name | None = None
    date_of_birth: BirthDate | None = None
    country: str | None = Field(default=None, min_length=2, max_length=2)
    city: City | None = None

    @field_validator("full_name", "city")
    @classmethod
    def _clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = normalise_whitespace(value)
        if len(cleaned) < 2:
            raise ValueError("must contain at least 2 non-space characters")
        return cleaned

    @field_validator("country")
    @classmethod
    def _validate_country(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalise_country(value, allowed=COUNTRY_CODES)

    @field_validator("date_of_birth")
    @classmethod
    def _validate_date_of_birth(cls, value: date | None) -> date | None:
        return None if value is None else validate_driver_birth_date(value)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    date_of_birth: date
    country: str
    city: str
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def age(self) -> int:
        """Derived, so it can never drift from the stored date of birth."""
        return years_since(self.date_of_birth)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(Token):
    """Issued on both registration and login so the UI needs one round trip."""

    user: UserRead
