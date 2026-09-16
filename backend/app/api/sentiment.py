from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Comment, SentimentAnalysis

router = APIRouter(prefix="/api/sentiment", tags=["sentiment"])

SENTIMENT_LABELS = ["positive", "neutral", "negative", "mixed"]


def _breakdown(rows: list[tuple[str, int]]) -> dict:
    counts = {label: 0 for label in SENTIMENT_LABELS}
    for sentiment, count in rows:
        if sentiment in counts:
            counts[sentiment] = count
    total = sum(counts.values())
    result = {f"{label}_pct": round(100 * counts[label] / total, 1) if total else 0.0 for label in SENTIMENT_LABELS}
    result["total"] = total
    return result


@router.get("")
def sentiment_breakdown(db: Session = Depends(get_db)):
    """Overall sentiment split plus a per-platform breakdown — the same
    per-platform numbers double as the platform comparison table in
    spec section 16."""
    overall_rows = (
        db.query(SentimentAnalysis.sentiment, func.count())
        .join(Comment)
        .filter(Comment.is_relevant.is_(True))
        .group_by(SentimentAnalysis.sentiment)
        .all()
    )

    platform_rows = (
        db.query(Comment.platform, SentimentAnalysis.sentiment, func.count())
        .join(SentimentAnalysis, SentimentAnalysis.comment_id == Comment.id)
        .filter(Comment.is_relevant.is_(True))
        .group_by(Comment.platform, SentimentAnalysis.sentiment)
        .all()
    )

    by_platform: dict[str, list[tuple[str, int]]] = {}
    for platform, sentiment, count in platform_rows:
        by_platform.setdefault(platform, []).append((sentiment, count))

    return {
        "overall": _breakdown(overall_rows),
        "by_platform": [{"platform": platform, **_breakdown(rows)} for platform, rows in by_platform.items()],
    }
