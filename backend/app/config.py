from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/packages_monitor"

    apify_api_token: str = ""
    apify_linkedin_actor: str = ""
    apify_facebook_actor: str = ""
    apify_instagram_actor: str = ""
    # Apify fallback for Reddit — only used if REDDIT_CLIENT_ID/SECRET below
    # aren't set (Reddit's free API needs "Responsible Builder Policy"
    # approval as of 2026, so this covers the wait).
    apify_reddit_actor: str = ""

    # Preferred, free path for Reddit: a "script" app at
    # https://www.reddit.com/prefs/apps. Self-service creation is currently
    # gated behind Reddit's approval process — see README.
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "packages-group-monitor/1.0"

    max_posts_per_run: int = 20
    max_comments_per_run: int = 100
    max_run_cost_usd: float = 0.50
    collection_interval_minutes: int = 60
    # Off by default — scheduled collection burns Apify usage unattended,
    # so it's an explicit opt-in rather than something that starts itself
    # the moment real actor IDs/tokens are configured (spec section 23).
    enable_scheduler: bool = False

    # Canonical company names only — this is what gets sent AS SEARCH
    # QUERIES to each collector (Reddit/LinkedIn/Instagram fan out one
    # actor search per entry; Facebook uses just the first). Deliberately
    # kept short: searching a platform for "Pkg Mall" or "Packages Ltd"
    # finds essentially nothing a full-name search wouldn't, but tripling
    # the query count roughly triples run time/cost for no benefit — see
    # the 2026-09-09 incident below where 15 queries (the old, merged
    # list) pushed a Reddit run past the Apify client's own timeout after
    # it had already been charged for. Short forms are still caught — see
    # `relevance_keywords` below.
    search_keywords: str = (
        "Packages Group,Packages Limited,Packages Pakistan,Packages Mall,Packages Convertors,"
        "Packages Group Pakistan"
    )

    # Broader than `search_keywords` on purpose: this is the LOCAL filter
    # applied after collection (relevance.py), run against text a search
    # already found — so it's safe and useful to also catch short forms
    # ("Packages Ltd", "Pkgs Mall", etc.) here even though they'd be
    # wasteful as actual search queries above. See relevance.py for why
    # bare 2-3 letter acronyms ("PM", "PG") are deliberately left out even
    # from this broader list.
    relevance_keywords: str = (
        "Packages Group,Packages Limited,Packages Pakistan,Packages Mall,Packages Convertors,"
        "Packages Group Pakistan,Packages Grp,Packages Ltd,Packages Pak,Pkg Mall,Pkgs Mall,"
        "Packages Conv,Pkgs Convertors,Packages Grp Pakistan,Pkgs Group Pakistan"
    )
    spike_threshold_percent: int = 100

    backend_cors_origins: str = "http://localhost:5173"

    @property
    def search_keyword_list(self) -> list[str]:
        return [k.strip() for k in self.search_keywords.split(",") if k.strip()]

    @property
    def relevance_keyword_list(self) -> list[str]:
        return [k.strip() for k in self.relevance_keywords.split(",") if k.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]


settings = Settings()
