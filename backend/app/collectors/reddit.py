from datetime import datetime, timezone

import praw

from app.collectors.apify_client import ApifyClient
from app.collectors.base import SocialDataCollector
from app.config import settings


class RedditCollector(SocialDataCollector):
    """Reddit collector with a three-tier fallback, preferring the free
    option and only spending Apify budget when nothing free is available:

      1. Reddit's own official API (PRAW) — free, but as of 2026 requires
         Reddit's "Responsible Builder Policy" approval before you can even
         create OAuth credentials (self-service app creation is closed).
         Used automatically the moment REDDIT_CLIENT_ID/SECRET are set.
      2. Apify actor (APIFY_REDDIT_ACTOR) — pay-per-result, works today
         without waiting on Reddit's approval queue.
      3. Built-in sample data — keeps the pipeline testable with neither
         configured.

    Implements SocialDataCollector directly (not ApifyCollector) since it
    isn't purely Apify-backed, but tier 2 reuses ApifyClient directly.
    """

    platform = "reddit"

    # How many of a matching post's comments to scan for keyword hits
    # (official-API tier only — Apify's actor searches comments directly).
    COMMENTS_SCANNED_PER_POST = 30

    def __init__(
        self, praw_client: "praw.Reddit | None" = None, apify_client: ApifyClient | None = None
    ):
        self._praw_client = praw_client
        self._apify_client = apify_client

    def collect(self, keywords: list[str], max_items: int) -> list[dict]:
        max_items = min(max_items, settings.max_comments_per_run)

        client = self._get_praw_client()
        if client is not None:
            return self._collect_via_reddit_api(client, keywords, max_items)

        if settings.apify_api_token and settings.apify_reddit_actor:
            return self._collect_via_apify(keywords, max_items)

        return self._sample_data()[:max_items]

    # --- Tier 1: free official Reddit API --------------------------------

    def _get_praw_client(self):
        if self._praw_client is not None:
            return self._praw_client
        if not (settings.reddit_client_id and settings.reddit_client_secret):
            return None
        self._praw_client = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
        )
        return self._praw_client

    def _collect_via_reddit_api(self, client, keywords: list[str], max_items: int) -> list[dict]:
        items: list[dict] = []
        seen_post_ids: set[str] = set()
        seen_comment_ids: set[str] = set()
        per_keyword_limit = max(1, max_items // max(len(keywords), 1))

        for keyword in keywords:
            if len(items) >= max_items:
                break

            for submission in client.subreddit("all").search(
                keyword, sort="new", limit=per_keyword_limit
            ):
                if submission.id not in seen_post_ids:
                    seen_post_ids.add(submission.id)
                    items.append(self._normalize_post(submission))
                    if len(items) >= max_items:
                        break

                submission.comments.replace_more(limit=0)
                for comment in submission.comments.list()[: self.COMMENTS_SCANNED_PER_POST]:
                    if comment.id in seen_comment_ids:
                        continue
                    if not _mentions_any(comment.body, keywords):
                        continue
                    seen_comment_ids.add(comment.id)
                    items.append(self._normalize_comment(comment, submission))
                    if len(items) >= max_items:
                        break

                if len(items) >= max_items:
                    break

        return items[:max_items]

    # --- Tier 2: Apify fallback --------------------------------------------

    def _collect_via_apify(self, keywords: list[str], max_items: int) -> list[dict]:
        client = self._apify_client or ApifyClient(settings.apify_api_token)
        run_input = {
            # Live-tested: this actor takes ~2.5 minutes PER search term
            # (crawl-and-search, not a flat-rate lookup), so passing all 6
            # keywords made two consecutive runs each hit our 600s abort
            # ceiling without finishing even one full pass. One primary
            # keyword — same tradeoff Facebook's collector already makes,
            # same reasoning — keeps a real run fast enough to actually
            # complete; the broader relevance_keywords list (short forms
            # included) still applies locally to whatever comes back.
            #
            # Quoted, though live-tested this does NOT get exact-phrase
            # matching out of this actor/Reddit's search — confirmed via
            # the actual run's stored INPUT that the quotes reach the
            # actor intact, yet results still keep coming back as
            # stemmed/fuzzy matches on "package"+"group" nearby rather
            # than the literal phrase (car-part and Linux-package-manager
            # comments, a dating-subreddit post, an 18+ roleplay
            # disclaimer — never actually about the company). Left quoted
            # since it's harmless and may still narrow other actors/
            # queries; the real mitigation is that relevance.py's local
            # filter is what actually keeps this noise off the dashboard
            # — Reddit's real signal-to-noise for a common two-word name
            # like "Packages Group" is just low with this actor.
            "searches": [f'"{kw}"' for kw in keywords[:1]],
            "searchPosts": True,
            "searchComments": True,
            "maxItems": min(max_items, 30),
            # "maxComments" scales per-post, not as a flat total, so it
            # multiplies with maxItems fast — capped separately and much
            # lower (matches COMMENTS_SCANNED_PER_POST above).
            "maxComments": 10,
        }
        raw_items = client.run_actor_sync(
            settings.apify_reddit_actor, run_input, max_total_charge_usd=settings.max_run_cost_usd
        )
        return [self._normalize_apify_item(item) for item in raw_items][:max_items]

    def _normalize_apify_item(self, raw_item: dict) -> dict:
        # Matches trudax/reddit-scraper-lite's input/output schema (verified
        # against its Apify Store listing). Adjust if a different actor is
        # chosen for APIFY_REDDIT_ACTOR.
        is_comment = "body" in raw_item or raw_item.get("dataType") == "comment"
        text = raw_item.get("body") or raw_item.get("text") or raw_item.get("title") or ""

        created = raw_item.get("createdAt") or raw_item.get("created_utc")
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
            "source_type": "comment" if is_comment else "post",
            "post_id": raw_item.get("postId") or raw_item.get("parentId"),
            "comment_id": raw_item.get("id") if is_comment else None,
            "post_url": raw_item.get("postUrl") or raw_item.get("url"),
            "comment_url": raw_item.get("url") if is_comment else None,
            "text": text,
            "author_name": raw_item.get("username") or raw_item.get("author"),
            "created_at": created_at,
            "engagement": raw_item.get("score") or raw_item.get("upVotes") or 0,
        }

    def _normalize_post(self, submission) -> dict:
        text = submission.title
        if submission.selftext:
            text = f"{text}\n{submission.selftext}"
        return {
            "platform": self.platform,
            "source_type": "post",
            "post_id": submission.id,
            "comment_id": None,
            "post_url": f"https://reddit.com{submission.permalink}",
            "comment_url": None,
            "text": text,
            "author_name": str(submission.author) if submission.author else None,
            "created_at": datetime.fromtimestamp(submission.created_utc, tz=timezone.utc),
            "engagement": submission.score,
        }

    def _normalize_comment(self, comment, submission) -> dict:
        return {
            "platform": self.platform,
            "source_type": "comment",
            "post_id": submission.id,
            "comment_id": comment.id,
            "post_url": f"https://reddit.com{submission.permalink}",
            "comment_url": f"https://reddit.com{comment.permalink}",
            "text": comment.body,
            "author_name": str(comment.author) if comment.author else None,
            "created_at": datetime.fromtimestamp(comment.created_utc, tz=timezone.utc),
            "engagement": comment.score,
        }

    def _sample_data(self) -> list[dict]:
        now = datetime.now(timezone.utc)
        return [
            {
                "platform": "reddit",
                "source_type": "comment",
                "post_id": "t3_sample1",
                "comment_id": "t1_sample1a",
                "post_url": "https://reddit.com/r/Pakistan/comments/sample1",
                "comment_url": "https://reddit.com/r/Pakistan/comments/sample1/_/sample1a",
                "text": "Packages Mall in Lahore has gotten so much better since the renovation.",
                "author_name": "sample_user_1",
                "created_at": now,
                "engagement": 12,
            },
            {
                "platform": "reddit",
                "source_type": "comment",
                "post_id": "t3_sample2",
                "comment_id": "t1_sample2a",
                "post_url": "https://reddit.com/r/Pakistan/comments/sample2",
                "comment_url": "https://reddit.com/r/Pakistan/comments/sample2/_/sample2a",
                "text": "Packages Limited customer service never responds to complaints, very disappointing.",
                "author_name": "sample_user_2",
                "created_at": now,
                "engagement": 4,
            },
            {
                "platform": "reddit",
                "source_type": "post",
                "post_id": "t3_sample3",
                "comment_id": None,
                "post_url": "https://reddit.com/r/business/comments/sample3",
                "comment_url": None,
                "text": "Packages Group announced a new sustainability initiative for their converting business.",
                "author_name": "sample_user_3",
                "created_at": now,
                "engagement": 25,
            },
            {
                "platform": "reddit",
                "source_type": "comment",
                "post_id": "t3_sample4",
                "comment_id": "t1_sample4a",
                "post_url": "https://reddit.com/r/Lahore/comments/sample4",
                "comment_url": "https://reddit.com/r/Lahore/comments/sample4/_/sample4a",
                "text": "I bought some packages yesterday for shipping, nothing to do with the company.",
                "author_name": "sample_user_4",
                "created_at": now,
                "engagement": 1,
            },
        ]


def _mentions_any(text: str, keywords: list[str]) -> bool:
    lowered = (text or "").lower()
    return any(keyword.lower() in lowered for keyword in keywords)
