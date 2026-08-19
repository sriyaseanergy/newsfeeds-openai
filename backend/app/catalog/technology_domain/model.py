from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from app.infrastructure.database.base import Base
from sqlalchemy import Boolean, DateTime, String, Text, UniqueConstraint, func, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.catalog.feed.model import Feed


class TechnologyDomainFrequency(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"


class TechnologyDomainSchedule(str, Enum):
    """Persisted schedule values, including system-only MANUAL."""

    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MANUAL = "MANUAL"


class InvalidTechnologyDomainFrequencyError(ValueError):
    """Raised when a frequency value is not DAILY or WEEKLY."""


def parse_technology_domain_frequency(value: object) -> TechnologyDomainFrequency:
    if isinstance(value, TechnologyDomainFrequency):
        return value
    if isinstance(value, TechnologyDomainSchedule):
        if value is TechnologyDomainSchedule.MANUAL:
            raise InvalidTechnologyDomainFrequencyError(
                "MANUAL is not a valid technology domain frequency."
            )
        return TechnologyDomainFrequency(value.value)
    if isinstance(value, str):
        normalized = value.strip().upper()
        try:
            return TechnologyDomainFrequency(normalized)
        except ValueError as exc:
            raise InvalidTechnologyDomainFrequencyError(
                f"Invalid technology domain frequency: {value!r}. "
                "Expected DAILY or WEEKLY."
            ) from exc
    raise InvalidTechnologyDomainFrequencyError(
        f"Invalid technology domain frequency: {value!r}. Expected DAILY or WEEKLY."
    )


class TechnologyDomain(Base):
    __tablename__ = "technology_domains"
    __table_args__ = (UniqueConstraint("slug", name="uq_technology_domains_slug"),)

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        "is_enabled",
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    frequency: Mapped[TechnologyDomainSchedule] = mapped_column(
        "schedule",
        SAEnum(TechnologyDomainSchedule, name="technology_domain_schedule"),
        nullable=False,
        default=TechnologyDomainSchedule.DAILY,
        server_default=TechnologyDomainSchedule.DAILY.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    feeds: Mapped[list["Feed"]] = relationship(
        back_populates="technology_domain",
        cascade="all, delete-orphan",
    )

    @property
    def is_enabled(self) -> bool:
        return self.is_active

    @is_enabled.setter
    def is_enabled(self, value: bool) -> None:
        self.is_active = value

    @property
    def schedule(self) -> TechnologyDomainSchedule:
        return self.frequency

    @schedule.setter
    def schedule(self, value: TechnologyDomainSchedule) -> None:
        self.frequency = value

    @property
    def configured_frequency(self) -> TechnologyDomainFrequency:
        return parse_technology_domain_frequency(self.frequency)
