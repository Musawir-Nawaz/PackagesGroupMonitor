"""One-off smoke test: exercise create/read/update/delete against every table.

Usage:
    ./venv/Scripts/python.exe test_crud.py

Cleans up after itself — safe to run repeatedly.
"""

from datetime import datetime, timezone

from app.database import SessionLocal
from app.models import Alert, CollectionRun, Comment, SentimentAnalysis


def main():
    db = SessionLocal()
    try:
        # CREATE
        comment = Comment(
            platform="reddit",
            source_type="comment",
            post_id="t3_test123",
            comment_id="t1_test456",
            post_url="https://reddit.com/r/test/comments/test123",
            comment_url="https://reddit.com/r/test/comments/test123/_/test456",
            text="Packages is doing a great job with their new sustainable packaging.",
            author_name="test_user",
            created_at=datetime.now(timezone.utc),
            engagement=5,
            is_relevant=True,
            dedup_key="reddit:t1_test456",
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        print(f"CREATE comment id={comment.id}")

        sentiment = SentimentAnalysis(
            comment_id=comment.id,
            sentiment="positive",
            confidence=0.93,
            severity=None,
            topic="Sustainability",
        )
        run = CollectionRun(
            platform="reddit",
            completed_at=datetime.now(timezone.utc),
            items_collected=1,
            items_new=1,
            items_duplicate=0,
            status="success",
        )
        alert = Alert(
            comment_id=comment.id,
            alert_type="topic_spike",
            severity="low",
            message="Smoke-test alert",
        )
        db.add_all([sentiment, run, alert])
        db.commit()
        print(f"CREATE sentiment id={sentiment.id}, run id={run.id}, alert id={alert.id}")

        # READ
        fetched = db.query(Comment).filter_by(id=comment.id).one()
        assert fetched.sentiment_analysis.sentiment == "positive"
        print("READ ok:", fetched.text[:40], "...")

        # UPDATE
        fetched.engagement = 10
        db.commit()
        db.refresh(fetched)
        assert fetched.engagement == 10
        print("UPDATE ok: engagement =", fetched.engagement)

        # DELETE (cascades to sentiment_analysis + alerts)
        db.delete(fetched)
        db.commit()
        assert db.query(Comment).filter_by(id=comment.id).first() is None
        assert db.query(SentimentAnalysis).filter_by(comment_id=comment.id).first() is None
        assert db.query(Alert).filter_by(comment_id=comment.id).first() is None
        print("DELETE ok: cascade removed sentiment + alert rows")

        db.delete(run)
        db.commit()

        print("\nAll CRUD operations succeeded.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
