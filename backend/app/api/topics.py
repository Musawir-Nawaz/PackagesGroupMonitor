from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Comment, SentimentAnalysis

router = APIRouter(prefix="/api/topics", tags=["topics"])


@router.get("")
def topic_breakdown(db: Session = Depends(get_db)):
    rows = (
        db.query(SentimentAnalysis.topic, SentimentAnalysis.sentiment, func.count())
        .join(Comment)
        .filter(Comment.is_relevant.is_(True))
        .group_by(SentimentAnalysis.topic, SentimentAnalysis.sentiment)
        .all()
    )

    topics: dict[str, dict] = {}
    for topic, sentiment, count in rows:
        entry = topics.setdefault(
            topic, {"topic": topic, "positive": 0, "neutral": 0, "negative": 0, "mixed": 0, "total": 0}
        )
        entry[sentiment] = count
        entry["total"] += count

    return sorted(topics.values(), key=lambda t: t["total"], reverse=True)
