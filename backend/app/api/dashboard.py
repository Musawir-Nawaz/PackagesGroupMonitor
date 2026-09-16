from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Comment, SentimentAnalysis
from app.services.analysis_pipeline import ALERT_SEVERITY_THRESHOLD

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

PERIOD_DAYS = {"today": 1, "7d": 7, "30d": 30, "90d": 90}


def _since(period: str) -> datetime:
    days = PERIOD_DAYS.get(period, 7)
    return datetime.now(timezone.utc) - timedelta(days=days)


@router.get("/summary")
def dashboard_summary(period: str = "7d", db: Session = Depends(get_db)):
    since = _since(period)

    base = (
        db.query(SentimentAnalysis)
        .join(Comment)
        .filter(Comment.is_relevant.is_(True), Comment.collected_at >= since)
    )

    total = base.count()
    counts = dict(
        base.with_entities(SentimentAnalysis.sentiment, func.count()).group_by(SentimentAnalysis.sentiment).all()
    )

    def pct(label: str) -> float:
        return round(100 * counts.get(label, 0) / total, 1) if total else 0.0

    platform_counts = (
        db.query(Comment.platform, func.count())
        .filter(Comment.is_relevant.is_(True), Comment.collected_at >= since)
        .group_by(Comment.platform)
        .all()
    )

    # Only genuinely high-risk comments — matches the threshold that raises
    # an alert (spec section 9's HIGH/CRITICAL bands), not just "top 10 by
    # severity" which could include LOW/MEDIUM ones.
    high_risk = (
        base.filter(SentimentAnalysis.severity > ALERT_SEVERITY_THRESHOLD)
        .order_by(SentimentAnalysis.severity.desc())
        .limit(10)
        .all()
    )

    return {
        "period": period,
        "total_mentions": total,
        "positive_pct": pct("positive"),
        "neutral_pct": pct("neutral"),
        "negative_pct": pct("negative"),
        "mixed_pct": pct("mixed"),
        "platform_breakdown": [{"platform": p, "count": c} for p, c in platform_counts],
        "high_risk_comments": [
            {
                "id": sa.comment.id,
                "platform": sa.comment.platform,
                "text": sa.comment.text,
                "sentiment": sa.sentiment,
                "severity": sa.severity,
                "topic": sa.topic,
                "created_at": sa.comment.created_at,
                "comment_url": sa.comment.comment_url or sa.comment.post_url,
            }
            for sa in high_risk
        ],
    }


@router.get("/trends")
def dashboard_trends(period: str = "30d", db: Session = Depends(get_db)):
    since = _since(period)

    rows = (
        db.query(func.date(Comment.collected_at).label("day"), SentimentAnalysis.sentiment, func.count())
        .join(SentimentAnalysis, SentimentAnalysis.comment_id == Comment.id)
        .filter(Comment.is_relevant.is_(True), Comment.collected_at >= since)
        .group_by("day", SentimentAnalysis.sentiment)
        .order_by("day")
        .all()
    )

    days: dict[str, dict] = {}
    for day, sentiment, count in rows:
        key = str(day)
        point = days.setdefault(key, {"date": key, "positive": 0, "neutral": 0, "negative": 0, "mixed": 0})
        point[sentiment] = count

    series = list(days.values())
    for point in series:
        point["total"] = point["positive"] + point["neutral"] + point["negative"] + point["mixed"]

    return {"period": period, "series": series}
