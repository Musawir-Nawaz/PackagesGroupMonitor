from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.collectors.base import SocialDataCollector
from app.config import settings
from app.models import Comment, CollectionRun
from app.services.analysis_pipeline import analyze_comment
from app.services.deduplication import compute_dedup_key
from app.services.relevance import is_relevant


def run_collection(
    db: Session, collector: SocialDataCollector, max_items: int | None = None
) -> CollectionRun:
    # Hard cap regardless of what's requested — the cost-protection floor
    # from spec section 23, enforced here so it applies to every collector.
    max_items = min(max_items or settings.max_comments_per_run, settings.max_comments_per_run)

    run = CollectionRun(platform=collector.platform, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        raw_items = collector.collect(settings.search_keyword_list, max_items)

        new_count = 0
        duplicate_count = 0
        # Tracks dedup_keys already staged in *this* run, alongside the DB
        # check below — the session has autoflush=False (database.py), so
        # a pending add() from earlier in this same loop is invisible to
        # query().filter_by() until the final commit(); without this, two
        # items colliding on the same key within one batch (e.g. two
        # post_id=None results both hashing to "reddit:post:None") reach
        # commit() together and the whole run's insert fails on the
        # unique constraint, discarding every row in the batch — not just
        # the dupes.
        seen_dedup_keys: set[str] = set()

        for item in raw_items:
            dedup_key = compute_dedup_key(item)
            if dedup_key in seen_dedup_keys:
                duplicate_count += 1
                continue
            already_exists = db.query(Comment).filter_by(dedup_key=dedup_key).first() is not None
            if already_exists:
                duplicate_count += 1
                continue
            seen_dedup_keys.add(dedup_key)

            comment = Comment(
                platform=item["platform"],
                source_type=item["source_type"],
                post_id=item.get("post_id"),
                comment_id=item.get("comment_id"),
                post_url=item.get("post_url"),
                comment_url=item.get("comment_url"),
                text=item["text"],
                author_name=item.get("author_name"),
                created_at=item.get("created_at"),
                engagement=item.get("engagement", 0),
                is_relevant=is_relevant(item["text"]),
                dedup_key=dedup_key,
            )
            db.add(comment)
            new_count += 1

            if comment.is_relevant:
                db.flush()  # assigns comment.id, needed for the sentiment_analysis FK
                analyze_comment(db, comment)

        run.items_collected = len(raw_items)
        run.items_new = new_count
        run.items_duplicate = duplicate_count
        run.status = "success"
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:
        # Covers collector.collect() failing AND any failure while staging
        # the insert loop above (e.g. a DB constraint violation) — either
        # way the run must not stay stuck at status="running" forever, so
        # this rolls back first (a failed flush/commit leaves the session
        # unusable otherwise) then records the real failure in its own
        # transaction.
        db.rollback()
        run.status = "failed"
        run.error_message = str(exc)
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise

    db.refresh(run)
    return run
