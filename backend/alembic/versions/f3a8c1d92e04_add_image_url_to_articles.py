"""add image_url to articles

Revision ID: f3a8c1d92e04
Revises: e1c4f8a9d2b3
Create Date: 2026-08-18 03:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f3a8c1d92e04"
down_revision: str | Sequence[str] | None = "e1c4f8a9d2b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("articles", sa.Column("image_url", sa.String(length=2048), nullable=True))


def downgrade() -> None:
    op.drop_column("articles", "image_url")
