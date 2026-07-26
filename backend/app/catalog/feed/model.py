from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from app.infrastructure.database.base import Base
from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.catalog.article.model import Article
    from app.catalog.technology_domain.model import TechnologyDomain


class FetchKind(str, Enum):
    RSS = "RSS"


class Feed(Base):
    __tablename__ = "feeds"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    technology_domain_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("technology_domains.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    fetch_kind: Mapped[FetchKind] = mapped_column(
        SAEnum(FetchKind, name="feed_fetch_kind"),
        nullable=False,
        default=FetchKind.RSS,
        server_default=FetchKind.RSS.value,
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

    technology_domain: Mapped["TechnologyDomain"] = relationship(back_populates="feeds")
    articles: Mapped[list["Article"]] = relationship(
        back_populates="feed",
        cascade="all, delete-orphan",
    )

