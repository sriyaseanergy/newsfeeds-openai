"""add schedule to technology domains

Revision ID: 18a1ad4248c5
Revises: 87ea698775ad
Create Date: 2026-07-26 21:54:28.269424

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "18a1ad4248c5"
down_revision: str | Sequence[str] | None = "87ea698775ad"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    schedule_enum = sa.Enum(
        "DAILY",
        "WEEKLY",
        "MANUAL",
        name="technology_domain_schedule",
    )

    # Create the PostgreSQL enum type
    schedule_enum.create(op.get_bind(), checkfirst=True)

    # Add the column
    op.add_column(
        "technology_domains",
        sa.Column(
            "schedule",
            schedule_enum,
            nullable=False,
            server_default="DAILY",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("technology_domains", "schedule")

    schedule_enum = sa.Enum(
        "DAILY",
        "WEEKLY",
        "MANUAL",
        name="technology_domain_schedule",
    )

    schedule_enum.drop(op.get_bind(), checkfirst=True)
