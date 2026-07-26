from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from app.infrastructure.database.base import Base
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.catalog.feed.model import Feed


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    feed_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("feeds.id"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    source_identifier: Mapped[str | None] = mapped_column(String(512), nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_processed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
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

    feed: Mapped["Feed"] = relationship(back_populates="articles")

