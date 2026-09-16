from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert
from app.services.trend_detection import detect_negative_spike

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def _serialize(alert: Alert) -> dict:
    comment = alert.comment
    return {
        "id": alert.id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "message": alert.message,
        "created_at": alert.created_at,
        "is_resolved": alert.is_resolved,
        "comment": {
            "id": comment.id,
            "platform": comment.platform,
            "text": comment.text,
            "post_url": comment.post_url,
            "comment_url": comment.comment_url,
        }
        if comment
        else None,
    }


@router.get("")
def list_alerts(is_resolved: bool | None = None, db: Session = Depends(get_db)):
    query = db.query(Alert)
    if is_resolved is not None:
        query = query.filter(Alert.is_resolved.is_(is_resolved))
    alerts = query.order_by(Alert.created_at.desc()).limit(100).all()

    return {
        "comment_alerts": [_serialize(a) for a in alerts],
        "negative_spike": detect_negative_spike(db),
    }


@router.get("/{alert_id}")
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter_by(id=alert_id).first()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return _serialize(alert)
