from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.collectors.facebook import FacebookCollector
from app.collectors.instagram import InstagramCollector
from app.collectors.linkedin import LinkedInCollector
from app.collectors.reddit import RedditCollector
from app.database import get_db
from app.models import CollectionRun
from app.services.collection_runner import run_collection

router = APIRouter(prefix="/api/collection", tags=["collection"])

COLLECTORS = {
    "reddit": RedditCollector,
    "facebook": FacebookCollector,
    "linkedin": LinkedInCollector,
    "instagram": InstagramCollector,
}


def _serialize(run: CollectionRun) -> dict:
    return {
        "id": run.id,
        "platform": run.platform,
        "status": run.status,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "items_collected": run.items_collected,
        "items_new": run.items_new,
        "items_duplicate": run.items_duplicate,
        "error_message": run.error_message,
    }


@router.post("/run")
def trigger_collection(platform: str = "reddit", db: Session = Depends(get_db)):
    collector_cls = COLLECTORS.get(platform)
    if collector_cls is None:
        raise HTTPException(
            status_code=400,
            detail=f"No collector configured for platform '{platform}'. Available: {list(COLLECTORS)}",
        )

    # Retries only on OSError, never on ApifyClientError/other real
    # failures (a 403/quota/actor error retrying just wastes another paid
    # Apify call for the same guaranteed outcome). OSError specifically is
    # a known-flaky Windows race — reproduced live as "[Errno 22] Invalid
    # argument" from FastAPI's request threadpool, intermittent (not
    # every-first-call, not library-specific: seen with both httpx and
    # requests), self-resolving on a bare retry every time it's been hit
    # so far. One retry, not a loop — this is a narrow, specific
    # workaround, not a general resilience mechanism.
    try:
        run = run_collection(db, collector_cls())
    except OSError:
        try:
            run = run_collection(db, collector_cls())
        except Exception as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return _serialize(run)


@router.get("/status")
def collection_status(limit: int = 20, db: Session = Depends(get_db)):
    runs = db.query(CollectionRun).order_by(CollectionRun.started_at.desc()).limit(limit).all()
    return [_serialize(run) for run in runs]
