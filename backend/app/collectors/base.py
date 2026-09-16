from abc import ABC, abstractmethod


class SocialDataCollector(ABC):
    """Interface every platform collector implements.

    Downstream code (normalization, relevance, sentiment, the dashboard)
    only ever talks to this interface, so an Apify-backed collector can
    later be swapped for an official-API-backed one without touching
    anything else in the pipeline (see spec section 29).
    """

    platform: str

    @abstractmethod
    def collect(self, keywords: list[str], max_items: int) -> list[dict]:
        """Return normalized comment/post dicts matching the section 6 schema."""
        raise NotImplementedError
