"""add slug to technology domains

Revision ID: d7e1a4c9b2f3
Revises: c4d8e2f1a9b0
Create Date: 2026-08-19 10:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d7e1a4c9b2f3"
down_revision: Union[str, Sequence[str], None] = "c4d8e2f1a9b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "technology_domains",
        sa.Column("slug", sa.String(length=255), nullable=True),
    )
    op.execute(
        """
        UPDATE technology_domains
        SET slug = trim(both '-' from regexp_replace(lower(trim(name)), '[^a-z0-9]+', '-', 'g'))
        WHERE slug IS NULL
        """
    )
    op.execute(
        """
        UPDATE technology_domains AS td
        SET slug = td.slug || '-' || substr(replace(td.id::text, '-', ''), 1, 8)
        WHERE td.id IN (
            SELECT id
            FROM (
                SELECT id,
                       row_number() OVER (PARTITION BY slug ORDER BY created_at, id) AS slug_rank
                FROM technology_domains
            ) ranked
            WHERE slug_rank > 1
        )
        """
    )
    op.alter_column("technology_domains", "slug", nullable=False)
    op.create_unique_constraint(
        "uq_technology_domains_slug",
        "technology_domains",
        ["slug"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "uq_technology_domains_slug",
        "technology_domains",
        type_="unique",
    )
    op.drop_column("technology_domains", "slug")
