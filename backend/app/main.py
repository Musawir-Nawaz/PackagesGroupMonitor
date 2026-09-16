import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import alerts, collection, comments, dashboard, sentiment, topics
from app.config import settings
from app.scheduler import start_scheduler, stop_scheduler

if sys.platform == "win32":
    # Windows' default ProactorEventLoop (needed elsewhere for subprocess
    # support) intermittently breaks blocking httpx calls made from
    # FastAPI's request threadpool with "OSError: [Errno 22] Invalid
    # argument" — reproduced only when running under uvicorn, not in a
    # standalone script or a plain ThreadPoolExecutor, once
    # ApifyClient.run_actor_sync started making multiple sequential
    # blocking calls (start run -> poll -> fetch dataset) instead of one.
    # The Selector loop doesn't share that Proactor/IOCP interaction and
    # is the standard workaround; must be set before uvicorn creates its
    # event loop, so this runs at import time, before Config/Server setup.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Packages Group Sentiment & Reputation Monitor", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(collection.router)
app.include_router(comments.router)
app.include_router(dashboard.router)
app.include_router(sentiment.router)
app.include_router(topics.router)
app.include_router(alerts.router)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "environment": settings.environment,
    }
