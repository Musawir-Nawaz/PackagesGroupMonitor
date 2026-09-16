import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.services.scheduled_collection import run_all_collections

logger = logging.getLogger("packages_monitor.scheduler")

scheduler = BackgroundScheduler()


def start_scheduler() -> None:
    if not settings.enable_scheduler:
        logger.info("Scheduler disabled (ENABLE_SCHEDULER=false) - collection stays manual")
        return

    scheduler.add_job(
        run_all_collections,
        "interval",
        minutes=settings.collection_interval_minutes,
        id="collection_run",
        max_instances=1,  # never let two runs overlap if one takes longer than the interval
        coalesce=True,  # if a run was missed (e.g. app was asleep), fire once, not a backlog
    )
    scheduler.start()
    logger.info("Scheduler started: collection runs every %d minute(s)", settings.collection_interval_minutes)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
