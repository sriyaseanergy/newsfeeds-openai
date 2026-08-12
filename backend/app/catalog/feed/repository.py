from uuid import UUID

from app.catalog.feed.model import Feed
from app.catalog.feed.schemas import FeedCreate, FeedUpdate
from sqlalchemy import select
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

    def list(self) -> list[Feed]:
        statement = select(Feed).order_by(Feed.created_at.desc())
        return list(self.db.execute(statement).scalars().all())

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

