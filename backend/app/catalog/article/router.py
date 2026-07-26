from uuid import UUID

from app.catalog.article.repository import ArticleRepository
from app.catalog.article.schemas import ArticleCreate, ArticleResponse, ArticleUpdate
from app.catalog.article.service import (
    ArticleDuplicateUrlError,
    ArticleFeedNotFoundError,
    ArticleNotFoundError,
    ArticleService,
)
from app.catalog.feed.repository import FeedRepository
from app.infrastructure.database.session import get_db
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/articles", tags=["Articles"])


def get_article_service(db: Session = Depends(get_db)) -> ArticleService:
    repository = ArticleRepository(db)
    feed_repository = FeedRepository(db)
    return ArticleService(repository, feed_repository)


@router.post("", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
def create_article(
    payload: ArticleCreate,
    service: ArticleService = Depends(get_article_service),
) -> ArticleResponse:
    try:
        return service.create(payload)
    except ArticleFeedNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ArticleDuplicateUrlError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("", response_model=list[ArticleResponse])
def list_articles(
    service: ArticleService = Depends(get_article_service),
) -> list[ArticleResponse]:
    return service.list()


@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(
    article_id: UUID,
    service: ArticleService = Depends(get_article_service),
) -> ArticleResponse:
    try:
        return service.get_by_id(article_id)
    except ArticleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/{article_id}", response_model=ArticleResponse)
def update_article(
    article_id: UUID,
    payload: ArticleUpdate,
    service: ArticleService = Depends(get_article_service),
) -> ArticleResponse:
    try:
        return service.update(article_id, payload)
    except ArticleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ArticleFeedNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ArticleDuplicateUrlError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(
    article_id: UUID,
    service: ArticleService = Depends(get_article_service),
) -> Response:
    try:
        service.delete(article_id)
    except ArticleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)

