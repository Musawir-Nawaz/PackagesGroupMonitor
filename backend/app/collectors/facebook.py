from datetime import datetime, timezone

from app.collectors.apify_collector import ApifyCollector
from app.config import settings


class FacebookCollector(ApifyCollector):
    platform = "facebook"

    @property
    def actor_id(self) -> str:
        return settings.apify_facebook_actor

    def _build_run_input(self, keywords: list[str], max_items: int) -> dict:
        # Matches scraper_one/facebook-posts-search's real input schema
        # (verified against its Apify Store listing). That actor takes a
        # single `query` string rather than an array — one run covers our
        # primary keyword, keeping cost to one run instead of N. Posts
        # only; per-post comments would need a second actor
        # (apify/facebook-comments-scraper) chained on the result URLs, a
        # future enhancement. Adjust here if a different actor is chosen
        # for APIFY_FACEBOOK_ACTOR — public pages/posts only, never
        # private groups or login-gated content.
        return {
            "query": keywords[0] if keywords else "",
            "resultsCount": min(max_items, settings.max_posts_per_run),
        }

    def _normalize(self, raw_item: dict) -> dict:
        text = raw_item.get("postText") or ""

        created = raw_item.get("timestamp")
        created_at = None
        if isinstance(created, (int, float)):
            created_at = datetime.fromtimestamp(created, tz=timezone.utc)
        elif isinstance(created, str):
            try:
                created_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except ValueError:
                created_at = None

        author = raw_item.get("author") or {}

        return {
            "platform": self.platform,
            "source_type": "post",
            "post_id": raw_item.get("postId"),
            "comment_id": None,
            "post_url": raw_item.get("url"),
            "comment_url": None,
            "text": text,
            "author_name": author.get("name"),
            "created_at": created_at,
            "engagement": raw_item.get("reactionsCount") or 0,
        }

    def _sample_data(self) -> list[dict]:
        now = datetime.now(timezone.utc)
        return [
            {
                "platform": "facebook",
                "source_type": "comment",
                "post_id": "fb_sample_post_1",
                "comment_id": "fb_sample_comment_1",
                "post_url": "https://facebook.com/PackagesLimited/posts/sample1",
                "comment_url": "https://facebook.com/PackagesLimited/posts/sample1?comment_id=1",
                "text": "Packages customer service has become terrible. I complained twice and nobody helped.",
                "author_name": "sample_fb_user_1",
                "created_at": now,
                "engagement": 8,
            },
            {
                "platform": "facebook",
                "source_type": "comment",
                "post_id": "fb_sample_post_2",
                "comment_id": "fb_sample_comment_2",
                "post_url": "https://facebook.com/PackagesMall/posts/sample2",
                "comment_url": "https://facebook.com/PackagesMall/posts/sample2?comment_id=2",
                "text": "Packages Mall's weekend event was fantastic, great job by the team!",
                "author_name": "sample_fb_user_2",
                "created_at": now,
                "engagement": 34,
            },
            {
                "platform": "facebook",
                "source_type": "post",
                "post_id": "fb_sample_post_3",
                "comment_id": None,
                "post_url": "https://facebook.com/PackagesLimited/posts/sample3",
                "comment_url": None,
                "text": "Packages Convertors is hiring for its Lahore plant, apply through the careers page.",
                "author_name": "Packages Limited",
                "created_at": now,
                "engagement": 15,
            },
        ]
