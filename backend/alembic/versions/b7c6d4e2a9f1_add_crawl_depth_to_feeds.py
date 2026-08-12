"""add crawl_depth to feeds

Revision ID: b7c6d4e2a9f1
Revises: 9f2d7d53c1a4
Create Date: 2026-08-02 23:08:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7c6d4e2a9f1"
down_revision: str | Sequence[str] | None = "9f2d7d53c1a4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "feeds",
        sa.Column(
            "crawl_depth",
            sa.Integer(),
            nullable=True,
            server_default=sa.text("1"),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("feeds", "crawl_depth")
