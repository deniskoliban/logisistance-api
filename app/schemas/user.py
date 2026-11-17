"""Pydantic schemas for auth and user profile."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.reference import COUNTRY_CODES, normalise_country, normalise_whitespace

Name = Annotated[str, Field(min_length=2, max_length=120)]
Age = Annotated[int, Field(ge=18, le=100, description="Driver age in years")]
City = Annotated[str, Field(min_length=2, max_length=120)]
Password = Annotated[str, Field(min_length=8, max_length=128)]


class UserRegister(BaseModel):
    email: EmailStr
    password: Password
    full_name: Name
    age: Age
    country: str = Field(min_length=2, max_length=2, description="ISO 3166-1 alpha-2 code")
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


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserUpdate(BaseModel):
    """Partial profile update. Unset fields are left untouched."""

    full_name: Name | None = None
    age: Age | None = None
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


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    age: int
    country: str
    city: str
    created_at: datetime
    updated_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(Token):
    """Issued on both registration and login so the UI needs one round trip."""

    user: UserRead
