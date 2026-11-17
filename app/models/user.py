from __future__ import annotations

from datetime import date

from sqlalchemy import Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)

    # Basic profile information collected at registration.
    full_name: Mapped[str] = mapped_column(nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    # Where the driver lives (ISO 3166-1 alpha-2).
    country: Mapped[str] = mapped_column(index=True, nullable=False)
    # Where the carrier company is registered; often a different country.
    company_country: Mapped[str] = mapped_column(index=True, nullable=False)
    city: Mapped[str] = mapped_column(nullable=False)

    vehicles: Mapped[list["Vehicle"]] = relationship(  # noqa: F821
        back_populates="owner", cascade="all, delete-orphan", order_by="Vehicle.id"
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<User id={self.id} email={self.email!r}>"
