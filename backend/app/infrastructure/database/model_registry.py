"""
Central SQLAlchemy model registry for Alembic autogenerate.
Import feature models here so they are attached to Base.metadata.
"""

from app.catalog.technology_domain import TechnologyDomain

__all__ = ["TechnologyDomain"]

