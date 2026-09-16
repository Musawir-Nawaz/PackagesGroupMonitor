from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Comment, SentimentAnalysis

router = APIRouter(prefix="/api/comments", tags=["comments"])


def _serialize(comment: Comment) -> dict:
    sentiment = comment.sentiment_analysis
    return {
        "id": comment.id,
        "platform": comment.platform,
        "source_type": comment.source_type,
        "text": comment.text,
        "author_name": comment.author_name,
        "post_url": comment.post_url,
        "comment_url": comment.comment_url,
        "created_at": comment.created_at,
        "collected_at": comment.collected_at,
        "engagement": comment.engagement,
        "is_relevant": comment.is_relevant,
        "sentiment": sentiment.sentiment if sentiment else None,
        "confidence": float(sentiment.confidence) if sentiment else None,
        "severity": sentiment.severity if sentiment else None,
        "topic": sentiment.topic if sentiment else None,
    }


@router.get("")
def list_comments(
    platform: str | None = None,
    sentiment: str | None = None,
    topic: str | None = None,
    severity_min: int | None = None,
    days: int | None = None,
    search: str | None = None,
    # Defaults to showing everything actually collected, not just what
    # cleared the relevance filter — a run reporting "40 collected" with
    # this defaulted to True silently showed 0 of them whenever the
    # keyword-only filter (a known-imprecise heuristic, see
    # relevance.py) didn't recognize any as on-topic, which read as
    # "nothing was fetched" rather than "found, but not classified
    # relevant". Opt into relevant_only=true to narrow down instead.
    relevant_only: bool = False,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(Comment).outerjoin(SentimentAnalysis).options(joinedload(Comment.sentiment_analysis))

    if relevant_only:
        query = query.filter(Comment.is_relevant.is_(True))
    if platform:
        query = query.filter(Comment.platform == platform)
    if sentiment:
        query = query.filter(SentimentAnalysis.sentiment == sentiment)
    if topic:
        query = query.filter(SentimentAnalysis.topic == topic)
    if severity_min is not None:
        query = query.filter(SentimentAnalysis.severity >= severity_min)
    if days is not None:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        query = query.filter(Comment.collected_at >= since)
    if search:
        query = query.filter(Comment.text.ilike(f"%{search}%"))

    total = query.count()
    comments = query.order_by(Comment.collected_at.desc()).offset(offset).limit(limit).all()
    return {"total": total, "items": [_serialize(c) for c in comments]}


@router.get("/{comment_id}")
def get_comment(comment_id: int, db: Session = Depends(get_db)):
    comment = db.query(Comment).filter_by(id=comment_id).first()
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    return _serialize(comment)
