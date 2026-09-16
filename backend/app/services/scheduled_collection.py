import logging

from app.collectors.facebook import FacebookCollector
from app.collectors.instagram import InstagramCollector
from app.collectors.linkedin import LinkedInCollector
from app.collectors.reddit import RedditCollector
from app.database import SessionLocal
from app.services.collection_runner import run_collection

logger = logging.getLogger("packages_monitor.scheduler")

# Order matches the collection flow in spec section 21.
PLATFORM_COLLECTORS = [
    ("linkedin", LinkedInCollector),
    ("reddit", RedditCollector),
    ("facebook", FacebookCollector),
    ("instagram", InstagramCollector),
]


def run_all_collections() -> None:
    """Run every platform's collector once, each in its own DB session so
    one platform failing doesn't block or roll back the others."""
    for platform, collector_cls in PLATFORM_COLLECTORS:
        db = SessionLocal()
        try:
            run = run_collection(db, collector_cls())
            logger.info(
                "collection run: platform=%s status=%s new=%d duplicate=%d",
                platform,
                run.status,
                run.items_new,
                run.items_duplicate,
            )
        except Exception:
            logger.exception("collection run failed: platform=%s", platform)
        finally:
            db.close()
