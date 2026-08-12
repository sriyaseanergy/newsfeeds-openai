"""add crawl fetch kind value

Revision ID: 9f2d7d53c1a4
Revises: 8239003eebe6
Create Date: 2026-08-02 22:20:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9f2d7d53c1a4"
down_revision: str | Sequence[str] | None = "8239003eebe6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE feed_fetch_kind ADD VALUE IF NOT EXISTS 'CRAWL'")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("UPDATE feeds SET fetch_kind = 'RSS' WHERE fetch_kind::text = 'CRAWL'")
    op.execute("ALTER TYPE feed_fetch_kind RENAME TO feed_fetch_kind_old")
    op.execute("CREATE TYPE feed_fetch_kind AS ENUM ('RSS')")
    op.execute(
        """
        ALTER TABLE feeds
        ALTER COLUMN fetch_kind TYPE feed_fetch_kind
        USING fetch_kind::text::feed_fetch_kind
        """
    )
    op.execute("ALTER TABLE feeds ALTER COLUMN fetch_kind SET DEFAULT 'RSS'")
    op.execute("DROP TYPE feed_fetch_kind_old")
