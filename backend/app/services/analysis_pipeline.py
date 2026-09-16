from sqlalchemy.orm import Session

from app.models import Alert, Comment, SentimentAnalysis
from app.services.sentiment import analyze_sentiment
from app.services.severity import compute_severity, severity_label
from app.services.topic import classify_topic

# Alerts fire for HIGH/CRITICAL severity only (score > 60) — see spec
# section 9's bands and section 15's "high-severity comment" / "critical
# comment" alert categories.
ALERT_SEVERITY_THRESHOLD = 60
CRITICAL_THRESHOLD = 80


def analyze_comment(db: Session, comment: Comment) -> SentimentAnalysis:
    """Run relevance's downstream pipeline (sentiment -> severity -> topic)
    for one comment, persist the result, and raise an alert if warranted.

    Assumes `comment` already has a primary key (i.e. has been flushed).
    """
    result = analyze_sentiment(comment.text)
    sentiment = result["sentiment"]
    confidence = result["confidence"]

    # Severity is only meaningful for negative/mixed content — a positive
    # or neutral comment isn't a reputation risk regardless of confidence.
    severity = compute_severity(comment.text, confidence) if sentiment in ("negative", "mixed") else None
    topic = classify_topic(comment.text)

    analysis = SentimentAnalysis(
        comment_id=comment.id,
        sentiment=sentiment,
        confidence=confidence,
        severity=severity,
        topic=topic,
    )
    db.add(analysis)

    if severity is not None and severity > ALERT_SEVERITY_THRESHOLD:
        alert_type = "critical" if severity > CRITICAL_THRESHOLD else "high_severity"
        label = severity_label(severity)
        db.add(
            Alert(
                comment_id=comment.id,
                alert_type=alert_type,
                severity=label,
                message=f"{label} severity {sentiment} comment on {comment.platform}: {comment.text[:200]}",
            )
        )

    return analysis
