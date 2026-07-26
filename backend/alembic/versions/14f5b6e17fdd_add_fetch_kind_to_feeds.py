"""add fetch_kind to feeds

Revision ID: 14f5b6e17fdd
Revises: 18a1ad4248c5
Create Date: 2026-07-26 22:43:35.373960

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "14f5b6e17fdd"
down_revision: str | Sequence[str] | None = "18a1ad4248c5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Explicit PostgreSQL enum
feed_fetch_kind = sa.Enum(
    "RSS",
    name="feed_fetch_kind",
)


def upgrade() -> None:
    """Upgrade schema."""

    # Create enum type if it doesn't already exist
    feed_fetch_kind.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "articles",
        sa.Column(
            "source_identifier",
            sa.String(length=512),
            nullable=True,
        ),
    )

    op.add_column(
        "feeds",
        sa.Column(
            "fetch_kind",
            feed_fetch_kind,
            server_default="RSS",
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("feeds", "fetch_kind")
    op.drop_column("articles", "source_identifier")

    # Drop enum type
    feed_fetch_kind.drop(op.get_bind(), checkfirst=True)
