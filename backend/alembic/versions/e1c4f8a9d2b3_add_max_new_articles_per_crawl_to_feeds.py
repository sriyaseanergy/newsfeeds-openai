"""add max_new_articles_per_crawl to feeds

Revision ID: e1c4f8a9d2b3
Revises: b7c6d4e2a9f1
Create Date: 2026-08-03 02:25:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1c4f8a9d2b3"
down_revision: str | Sequence[str] | None = "b7c6d4e2a9f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "feeds",
        sa.Column(
            "max_new_articles_per_crawl",
            sa.Integer(),
            nullable=True,
            server_default=sa.text("20"),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("feeds", "max_new_articles_per_crawl")
