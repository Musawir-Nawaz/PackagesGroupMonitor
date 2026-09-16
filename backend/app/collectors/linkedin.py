from datetime import datetime, timezone

from app.collectors.apify_collector import ApifyCollector
from app.config import settings


class LinkedInCollector(ApifyCollector):
    platform = "linkedin"

    @property
    def actor_id(self) -> str:
        return settings.apify_linkedin_actor

    def _build_run_input(self, keywords: list[str], max_items: int) -> dict:
        # Matches harvestapi/linkedin-post-search's real input schema
        # (verified against its Apify Store listing). This actor nests
        # each post's comments inside it (comments[]) rather than
        # returning flat rows, so _normalize_all below flattens them.
        # Adjust here if a different actor is chosen for APIFY_LINKEDIN_ACTOR
        # — publicly visible posts/comments only, no authenticated
        # scraping of private profiles or connections-only content.
        return {
            "searchQueries": keywords,
            # maxPosts is per search query, not a total — capped by the
            # dedicated (much smaller) MAX_POSTS_PER_RUN, not the overall
            # comments budget, so N keywords can't multiply the actual
            # scrape volume far past what was intended.
            "maxPosts": min(max_items, settings.max_posts_per_run),
            "scrapeComments": True,
        }

    def _parse_date(self, value):
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value / 1000 if value > 10**12 else value, tz=timezone.utc)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    def _normalize_all(self, raw_items: list[dict]) -> list[dict]:
        normalized = []
        for post in raw_items:
            post_id = post.get("id")
            post_url = post.get("linkedinUrl")

            normalized.append(
                {
                    "platform": self.platform,
                    "source_type": "post",
                    "post_id": post_id,
                    "comment_id": None,
                    "post_url": post_url,
                    "comment_url": None,
                    "text": post.get("content") or "",
                    "author_name": (post.get("author") or {}).get("name"),
                    "created_at": self._parse_date((post.get("postedAt") or {}).get("date")),
                    "engagement": (post.get("engagement") or {}).get("likes") or 0,
                }
            )

            for comment in post.get("comments") or []:
                normalized.append(
                    {
                        "platform": self.platform,
                        "source_type": "comment",
                        "post_id": post_id,
                        "comment_id": comment.get("id"),
                        "post_url": post_url,
                        "comment_url": post_url,
                        "text": comment.get("commentary") or "",
                        "author_name": (comment.get("actor") or {}).get("name"),
                        "created_at": None,
                        "engagement": 0,
                    }
                )

        return normalized

    def _sample_data(self) -> list[dict]:
        now = datetime.now(timezone.utc)
        return [
            {
                "platform": "linkedin",
                "source_type": "post",
                "post_id": "li_sample_post_1",
                "comment_id": None,
                "post_url": "https://linkedin.com/company/packages-group/posts/sample1",
                "comment_url": None,
                "text": "Packages Group Pakistan announced record growth in its converting business this quarter.",
                "author_name": "Packages Group",
                "created_at": now,
                "engagement": 210,
            },
            {
                "platform": "linkedin",
                "source_type": "comment",
                "post_id": "li_sample_post_1",
                "comment_id": "li_sample_comment_1",
                "post_url": "https://linkedin.com/company/packages-group/posts/sample1",
                "comment_url": "https://linkedin.com/company/packages-group/posts/sample1?commentId=1",
                "text": "Congratulations to the Packages Limited team, well deserved after a tough year.",
                "author_name": "sample_li_user_1",
                "created_at": now,
                "engagement": 5,
            },
            {
                "platform": "linkedin",
                "source_type": "comment",
                "post_id": "li_sample_post_2",
                "comment_id": "li_sample_comment_2",
                "post_url": "https://linkedin.com/company/packages-group/posts/sample2",
                "comment_url": "https://linkedin.com/company/packages-group/posts/sample2?commentId=2",
                "text": "Packages management has ignored employee concerns about the new shift schedule for months.",
                "author_name": "sample_li_user_2",
                "created_at": now,
                "engagement": 12,
            },
        ]
