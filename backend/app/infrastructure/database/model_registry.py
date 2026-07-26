"""
Central SQLAlchemy model registry for Alembic autogenerate.
Import feature models here so they are attached to Base.metadata.
"""

from app.catalog.technology_domain import TechnologyDomain
from app.catalog.feed import Feed

__all__ = ["TechnologyDomain", "Feed"]

