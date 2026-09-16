from abc import abstractmethod

from app.collectors.apify_client import ApifyClient
from app.collectors.base import SocialDataCollector
from app.config import settings


class ApifyCollector(SocialDataCollector):
    """Base class for every platform collector backed by an Apify Actor.

    Handles the shared cost-protection and fallback logic (spec section 23):
    always clamp to MAX_COMMENTS_PER_RUN, and fall back to sample data
    instead of failing when no token/actor is configured yet — so the
    pipeline stays testable before a real Actor has been picked.
    """

    def __init__(self, client: ApifyClient | None = None):
        self.client = client

    @property
    @abstractmethod
    def actor_id(self) -> str:
        raise NotImplementedError

    def collect(self, keywords: list[str], max_items: int) -> list[dict]:
        max_items = min(max_items, settings.max_comments_per_run)

        if not settings.apify_api_token or not self.actor_id:
            return self._sample_data()[:max_items]

        client = self.client or ApifyClient(settings.apify_api_token)
        run_input = self._build_run_input(keywords, max_items)
        raw_items = client.run_actor_sync(
            self.actor_id, run_input, max_total_charge_usd=settings.max_run_cost_usd
        )
        return self._normalize_all(raw_items)[:max_items]

    @abstractmethod
    def _build_run_input(self, keywords: list[str], max_items: int) -> dict:
        raise NotImplementedError

    def _normalize_all(self, raw_items: list[dict]) -> list[dict]:
        """Default: one normalized item per raw item. Override this
        (instead of/alongside `_normalize`) when an actor nests multiple
        normalizable items per raw item — e.g. a post with embedded
        comments — and needs to flatten them into separate rows."""
        return [self._normalize(item) for item in raw_items]

    def _normalize(self, raw_item: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def _sample_data(self) -> list[dict]:
        raise NotImplementedError
