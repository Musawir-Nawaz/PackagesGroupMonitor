from datetime import datetime, timezone

from app.collectors.apify_collector import ApifyCollector
from app.config import settings


class InstagramCollector(ApifyCollector):
    platform = "instagram"

    @property
    def actor_id(self) -> str:
        return settings.apify_instagram_actor

    def _build_run_input(self, keywords: list[str], max_items: int) -> dict:
        # Matches apify/instagram-hashtag-scraper's real input schema
        # (verified against its Apify Store listing). Instagram's public
        # scraping surface is hashtag-based, not free-text search, so each
        # keyword is turned into a hashtag (spaces stripped: "Packages
        # Mall" -> "packagesmall"). Posts/reels only; per-post comments
        # would need a second actor (apify/instagram-comment-scraper)
        # chained on the result URLs, a future enhancement. Adjust here if
        # a different actor is chosen for APIFY_INSTAGRAM_ACTOR — public
        # content only, never private accounts.
        return {
            "hashtags": [kw.replace(" ", "").lower() for kw in keywords],
            "resultsType": "posts",
            "resultsLimit": min(max_items, settings.max_posts_per_run),
        }

    def _normalize(self, raw_item: dict) -> dict:
        text = raw_item.get("caption") or ""

        created = raw_item.get("timestamp")
        created_at = None
        if isinstance(created, (int, float)):
            created_at = datetime.fromtimestamp(created, tz=timezone.utc)
        elif isinstance(created, str):
            try:
                created_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except ValueError:
                created_at = None

        return {
            "platform": self.platform,
            "source_type": "post",
            "post_id": raw_item.get("id") or raw_item.get("shortCode"),
            "comment_id": None,
            "post_url": raw_item.get("url"),
            "comment_url": None,
            "text": text,
            "author_name": raw_item.get("ownerUsername"),
            "created_at": created_at,
            "engagement": raw_item.get("likesCount") or 0,
        }

    def _sample_data(self) -> list[dict]:
        now = datetime.now(timezone.utc)
        return [
            {
                "platform": "instagram",
                "source_type": "post",
                "post_id": "ig_sample_post_1",
                "comment_id": None,
                "post_url": "https://instagram.com/p/sample1",
                "comment_url": None,
                "text": "Packages Mall Lahore's new store opening this weekend! #PackagesMall",
                "author_name": "packagesmall",
                "created_at": now,
                "engagement": 540,
            },
            {
                "platform": "instagram",
                "source_type": "comment",
                "post_id": "ig_sample_post_1",
                "comment_id": "ig_sample_comment_1",
                "post_url": "https://instagram.com/p/sample1",
                "comment_url": "https://instagram.com/p/sample1/c/1",
                "text": "Love shopping at Packages Mall, best mall in Lahore!",
                "author_name": "sample_ig_user_1",
                "created_at": now,
                "engagement": 9,
            },
            {
                "platform": "instagram",
                "source_type": "comment",
                "post_id": "ig_sample_post_1",
                "comment_id": "ig_sample_comment_2",
                "post_url": "https://instagram.com/p/sample1",
                "comment_url": "https://instagram.com/p/sample1/c/2",
                "text": "Parking at Packages Mall is a nightmare, they really need to fix it.",
                "author_name": "sample_ig_user_2",
                "created_at": now,
                "engagement": 3,
            },
        ]
