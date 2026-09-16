from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Comment, SentimentAnalysis


def detect_negative_spike(db: Session, lookback_days: int = 7) -> dict | None:
    """Compare today's negative-comment count against the trailing daily
    average (spec section 12). Returns None if there isn't enough history
    yet, or the increase doesn't clear SPIKE_THRESHOLD_PERCENT.
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    baseline_start = today_start - timedelta(days=lookback_days)

    negative_query = db.query(Comment).join(SentimentAnalysis).filter(
        Comment.is_relevant.is_(True), SentimentAnalysis.sentiment == "negative"
    )

    today_count = negative_query.filter(Comment.collected_at >= today_start).count()
    baseline_count = negative_query.filter(
        Comment.collected_at >= baseline_start, Comment.collected_at < today_start
    ).count()

    baseline_avg = baseline_count / lookback_days
    if baseline_avg <= 0:
        return None

    increase_pct = round(100 * (today_count - baseline_avg) / baseline_avg, 1)
    if increase_pct < settings.spike_threshold_percent:
        return None

    top_topic_row = (
        db.query(SentimentAnalysis.topic, func.count())
        .join(Comment)
        .filter(SentimentAnalysis.sentiment == "negative", Comment.collected_at >= today_start)
        .group_by(SentimentAnalysis.topic)
        .order_by(func.count().desc())
        .first()
    )
    top_platform_row = (
        db.query(Comment.platform, func.count())
        .join(SentimentAnalysis)
        .filter(SentimentAnalysis.sentiment == "negative", Comment.collected_at >= today_start)
        .group_by(Comment.platform)
        .order_by(func.count().desc())
        .first()
    )

    return {
        "today_count": today_count,
        "baseline_avg": round(baseline_avg, 1),
        "increase_pct": increase_pct,
        "main_topic": top_topic_row[0] if top_topic_row else None,
        "main_platform": top_platform_row[0] if top_platform_row else None,
    }
