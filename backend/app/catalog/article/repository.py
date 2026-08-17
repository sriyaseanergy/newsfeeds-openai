from uuid import UUID

from app.catalog.article.model import Article
from app.catalog.article.schemas import ArticleCreate, ArticleUpdate
from sqlalchemy import select
from sqlalchemy.orm import Session


class ArticleRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: ArticleCreate) -> Article:
        data = payload.model_dump()
        data["url"] = str(payload.url)
        article = Article(**data)
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)
        return article

    def get_by_id(self, article_id: UUID) -> Article | None:
        statement = select(Article).where(Article.id == article_id)
        return self.db.execute(statement).scalar_one_or_none()

    def get_by_url(self, url: str) -> Article | None:
        statement = select(Article).where(Article.url == url)
        return self.db.execute(statement).scalar_one_or_none()

    def list(self) -> list[Article]:
        statement = select(Article).order_by(Article.created_at.desc())
        return list(self.db.execute(statement).scalars().all())

    def update(self, article: Article, payload: ArticleUpdate) -> Article:
        update_data = payload.model_dump(exclude_unset=True)
        if payload.url is not None:
            update_data["url"] = str(payload.url)

        for field, value in update_data.items():
            setattr(article, field, value)

        self.db.commit()
        self.db.refresh(article)
        return article

    def delete(self, article: Article) -> None:
        self.db.delete(article)
        self.db.commit()

    def mark_processed(self, article: Article) -> Article:
        article.is_processed = True
        self.db.commit()
        self.db.refresh(article)
        return article

