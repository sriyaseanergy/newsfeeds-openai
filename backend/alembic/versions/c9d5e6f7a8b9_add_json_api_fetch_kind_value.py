"""add json_api fetch kind value

Revision ID: c9d5e6f7a8b9
Revises: b8c3d4e5f6a7
Create Date: 2026-08-24 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "c9d5e6f7a8b9"
down_revision: Union[str, Sequence[str], None] = "b8c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE feed_fetch_kind ADD VALUE IF NOT EXISTS 'JSON_API'")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("UPDATE feeds SET fetch_kind = 'RSS' WHERE fetch_kind::text = 'JSON_API'")
    op.execute("ALTER TYPE feed_fetch_kind RENAME TO feed_fetch_kind_old")
    op.execute("CREATE TYPE feed_fetch_kind AS ENUM ('RSS', 'CRAWL')")
    op.execute(
        """
        ALTER TABLE feeds
        ALTER COLUMN fetch_kind TYPE feed_fetch_kind
        USING fetch_kind::text::feed_fetch_kind
        """
    )
    op.execute("ALTER TABLE feeds ALTER COLUMN fetch_kind SET DEFAULT 'RSS'")
    op.execute("DROP TYPE feed_fetch_kind_old")
