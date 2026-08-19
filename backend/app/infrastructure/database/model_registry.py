"""
Central SQLAlchemy model registry for Alembic autogenerate.
Import feature models here so they are attached to Base.metadata.
"""

from app.catalog.technology_domain import TechnologyDomain
from app.catalog.feed import Feed
from app.catalog.article import Article
from app.catalog.email_recipient import EmailRecipient
from app.catalog.user import User

__all__ = ["TechnologyDomain", "Feed", "Article", "EmailRecipient", "User"]

