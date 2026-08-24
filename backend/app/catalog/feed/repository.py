from __future__ import annotations

from uuid import UUID

from app.catalog.feed.model import Feed
from app.catalog.feed.schemas import FeedCreate, FeedUpdate
from sqlalchemy import func, select
from sqlalchemy.orm import Session


class FeedRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: FeedCreate) -> Feed:
        data = self._to_persisted_dict(payload)
        feed = Feed(**data)
        self.db.add(feed)
        self.db.commit()
        self.db.refresh(feed)
        return feed

    def get_by_id(self, feed_id: UUID) -> Feed | None:
        statement = select(Feed).where(Feed.id == feed_id)
        return self.db.execute(statement).scalar_one_or_none()

    def get_by_url(self, url: str) -> Feed | None:
        statement = select(Feed).where(Feed.url == url)
        return self.db.execute(statement).scalar_one_or_none()

    def list(self, technology_domain_id: UUID | None = None) -> list[Feed]:
        statement = select(Feed)
        if technology_domain_id is not None:
            statement = statement.where(Feed.technology_domain_id == technology_domain_id)
        statement = statement.order_by(Feed.created_at.desc())
        return list(self.db.execute(statement).scalars().all())

    def count_by_technology_domain_id(self, technology_domain_id: UUID) -> int:
        statement = (
            select(func.count())
            .select_from(Feed)
            .where(Feed.technology_domain_id == technology_domain_id)
        )
        return int(self.db.execute(statement).scalar_one())

    def count_by_technology_domain_ids(self, domain_ids: list[UUID]) -> dict[UUID, int]:
        if not domain_ids:
            return {}
        statement = (
            select(Feed.technology_domain_id, func.count())
            .where(Feed.technology_domain_id.in_(domain_ids))
            .group_by(Feed.technology_domain_id)
        )
        rows = self.db.execute(statement).all()
        return {domain_id: int(count) for domain_id, count in rows}

    def update(self, feed: Feed, payload: FeedUpdate) -> Feed:
        update_data = self._to_persisted_dict(payload, exclude_unset=True)

        for field, value in update_data.items():
            setattr(feed, field, value)

        self.db.commit()
        self.db.refresh(feed)
        return feed

    def delete(self, feed: Feed) -> None:
        self.db.delete(feed)
        self.db.commit()

    @staticmethod
    def _to_persisted_dict(payload: FeedCreate | FeedUpdate, exclude_unset: bool = False) -> dict:
        data = payload.model_dump(exclude_unset=exclude_unset)
        if "url" in data and payload.url is not None:
            data["url"] = str(payload.url)
        return data

