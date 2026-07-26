from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from app.infrastructure.database.base import Base
from sqlalchemy import Boolean, DateTime, String, Text, func, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.catalog.feed.model import Feed


class TechnologyDomainSchedule(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MANUAL = "MANUAL"


class TechnologyDomain(Base):
    __tablename__ = "technology_domains"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    schedule: Mapped[TechnologyDomainSchedule] = mapped_column(
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
