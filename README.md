# Packages Group Monitor

Social media sentiment & reputation monitoring prototype for Packages Group.
Collects publicly accessible mentions from LinkedIn, Reddit, Facebook, and
Instagram (via Apify), analyzes sentiment/topic/severity with open-source
NLP, and surfaces everything on a management dashboard.

Built incrementally — see [Development status](#development-status) for
what's done vs. planned.

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend:** React, Vite, Tailwind CSS, Recharts
- **Data collection:** Apify (LinkedIn/Facebook/Instagram always; Reddit too until its free official API is approved — see below)
- **NLP:** Hugging Face Transformers (open-source, local — no paid AI APIs)

## Project layout

```
backend/    FastAPI app (api/, collectors/, services/, models/)
frontend/   React + Vite dashboard
database/   SQL schema
```

## Getting started

### Database

Uses a local PostgreSQL 17 server (Windows service `postgresql-x64-17`,
installed via winget) with a dedicated `packages_monitor` database and
`packages_monitor_app` role — isolated from any other Postgres project on
this machine. The connection string lives in the root `.env` as
`DATABASE_URL` (never committed).

Schema lives in [database/schema.sql](database/schema.sql) (reference/manual
apply) and is mirrored by the SQLAlchemy models in `backend/app/models/`.

```bash
cd backend
./venv/Scripts/python.exe init_db.py     # creates tables from the models
./venv/Scripts/python.exe test_crud.py   # smoke-tests create/read/update/delete
```

### Backend

```bash
cd backend
python -m venv venv
./venv/Scripts/activate        # Windows
pip install -r requirements.txt
cp ../.env.example ../.env     # fill in real values, never commit .env
uvicorn app.main:app --reload --port 8000
```

Health check: `GET http://127.0.0.1:8000/api/health`

The sentiment model (~500MB) downloads from Hugging Face and is cached in
`~/.cache/huggingface` on first use — the first collection run after a
fresh install/restart takes a few seconds longer while it loads.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env           # points VITE_API_BASE_URL at the backend
npm run dev
```

Open `http://localhost:5173` — the dashboard shell shows a live
"Backend connection" indicator confirming it can reach the API.

### Running a collection

```
POST /api/collection/run?platform={reddit|facebook|linkedin|instagram}
GET  /api/collection/status                # recent collection_runs, newest first
```

Without credentials set in `.env`, every collector returns built-in
sample data so the relevance -> dedup -> DB pipeline stays testable
offline.

| Platform | Source | Scope |
|---|---|---|
| Reddit | Reddit official API (free) if `REDDIT_CLIENT_ID`/`SECRET` set, else Apify `trudax/reddit-scraper-lite`, else sample data | posts + comments either way |
| LinkedIn | Apify `harvestapi/linkedin-post-search` | posts + comments |
| Facebook | Apify `scraper_one/facebook-posts-search` | posts only (single query per run) |
| Instagram | Apify `apify/instagram-hashtag-scraper` | posts/reels only, hashtag-based |

**Reddit is the only platform with a genuine free public API**, so
`backend/app/collectors/reddit.py` tries it first, automatically. As of
2026, though, Reddit closed self-service API-app registration — creating
OAuth credentials now requires requesting access under Reddit's
["Responsible Builder Policy"](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy)
and waiting on approval (not guaranteed, no fixed timeline). Until/unless
that's approved, Reddit collection runs on the Apify actor instead — same
as LinkedIn/Facebook/Instagram, which have no free official equivalent at
all. **If you do get approved**, just set `REDDIT_CLIENT_ID` /
`REDDIT_CLIENT_SECRET` in `.env` and the collector switches to the free
path automatically — no code change needed.

Facebook and Instagram are posts-only for now — per-post comments on those
two would need a second chained actor (e.g.
`apify/facebook-comments-scraper`, `apify/instagram-comment-scraper`) run
against the discovered post URLs, which isn't built yet. All Apify actors
here are pay-per-result — check current pricing on each actor's Store
page before enabling scheduled collection, to stay inside the free-tier
budget.

To collect real data now: add `APIFY_API_TOKEN` to `.env` (get a free-tier
token at https://console.apify.com/account/integrations) — that alone
lights up all four platforms, Reddit included. If you swap in a different
Apify actor for any platform, that collector's `_build_run_input` /
`_normalize` (or `_normalize_apify_item` for Reddit) in
`backend/app/collectors/` will need adjusting to match the new actor's
schema.

## Cost controls

This project targets **$0 development cost**. Every Apify run is capped
two ways: `MAX_POSTS_PER_RUN`/`MAX_COMMENTS_PER_RUN` bound what each
collector asks an actor to scrape, and `MAX_RUN_COST_USD` is passed as
Apify's own `maxTotalChargeUsd` run parameter — a hard spend cap Apify
enforces server-side, so a wrong per-collector value can't run up an
unexpectedly large bill on its own (see incident below). Collection
defaults to manual runs until the pipeline is proven stable.
No paid AI APIs are used — sentiment analysis runs locally via open-source
models. Scheduled collection (`ENABLE_SCHEDULER=true` +
`COLLECTION_INTERVAL_MINUTES`) is opt-in and off by default for the same
reason — it shouldn't start consuming Apify usage unattended just because
a token got dropped into `.env`.

**Incident (2026-09-09):** while verifying the new Google collector against
a real (quota-exhausted) Apify account, a failed run's error message —
surfaced verbatim in the `/api/collection/run` 502 response and rendered
directly on the Platforms page — turned out to contain the full request URL
**including `APIFY_API_TOKEN` in plaintext** (`?token=...`), because
`ApifyClient` sent it as a query param and `httpx`'s exception message
includes the full URL. Affected every collector, not just Google. Fixed in
`backend/app/collectors/apify_client.py`: the token now goes in an
`Authorization: Bearer` header (Apify's own recommended method) instead of
the query string, and error messages are rebuilt from just the status code
— never the raw exception/URL. If your `.env`'s `APIFY_API_TOKEN` was ever
displayed on the Platforms page before this fix, treat it as exposed and
rotate it at https://console.apify.com/account/integrations.

**Incident (2026-09-08):** the very first real LinkedIn test run burned
the entire $5/month Apify free credit in two calls (~$7.51). Root cause:
`MAX_RUN_COST_USD` was defined in config but never actually passed to
Apify — pure dead config — and the LinkedIn collector's `maxPosts` was
wired to `MAX_COMMENTS_PER_RUN` (100) rather than the much smaller
`MAX_POSTS_PER_RUN` (20), so one run asked to scrape up to 100 posts per
search keyword. Both are fixed now (`maxTotalChargeUsd` wired into every
Apify call, `maxPosts`/`resultsCount`/`resultsLimit` all use
`MAX_POSTS_PER_RUN`) — noted here rather than silently patched, since it's
exactly the kind of gap between documented-intent and actual-enforcement
worth watching for elsewhere too.

## Development status

- [x] **Phase 1 — Project setup:** backend/frontend scaffolded, dashboard
      confirms live connection to the API.
- [x] **Phase 2 — Database:** local PostgreSQL 17, `comments` /
      `sentiment_analysis` / `collection_runs` / `alerts` tables created,
      CRUD verified end to end.
- [x] **Phase 3 — First Apify collector (Reddit):** collector ->
      relevance filter -> dedup -> DB pipeline verified end to end via
      `POST /api/collection/run?platform=reddit`. Runs on sample data
      until `APIFY_API_TOKEN` / `APIFY_REDDIT_ACTOR` are set in `.env`.
- [x] **Phase 4 — Remaining collectors (Facebook, LinkedIn, Instagram):**
      same `ApifyCollector` pattern as Reddit, all four verified end to end
      (collect -> relevance -> dedup -> DB), each running on sample data
      until its `APIFY_*_ACTOR` env var is set. Known limitation: the
      keyword-only relevance filter from section 7's suggested list can
      miss mentions that say just "Packages" + context (e.g. "Packages
      customer service...") rather than a full phrase like "Packages
      Limited" — closing that gap is what section 7's optional NLP
      relevance classifier (Phase 5) is for.
- [x] **Phase 5 — Sentiment/severity/topic pipeline:** every new relevant
      comment is automatically classified (positive/neutral/negative/mixed
      via `cardiffnlp/twitter-roberta-base-sentiment-latest`, run locally,
      no paid API), scored for severity (negative/mixed only — a lexicon +
      confidence heuristic, not just confidence), and tagged with a topic.
      HIGH/CRITICAL severity auto-raises an alert. Verified end to end
      against real inserted rows. Known model limitation: an ambiguous
      neutral-toned sentence ("I don't have enough information.") was
      misclassified negative rather than neutral — general-purpose social
      sentiment models are weak on this case; noted rather than papered
      over with a one-off keyword fix.
- [x] **Phase 6 — Full dashboard:** all 6 API endpoints from spec section
      20 (`/api/comments[/:id]`, `/api/dashboard/summary`,
      `/api/dashboard/trends`, `/api/sentiment`, `/api/topics`,
      `/api/alerts[/:id]`) built and verified against real data. Frontend
      has all 6 pages (Dashboard, Comments, Trends, Topics, Alerts,
      Platforms) with a sidebar shell, sentiment/platform charts, filters,
      and a comment detail panel — visually verified via headless
      Chromium screenshots of every page, zero console errors. One bug
      caught and fixed during that verification: the dashboard's
      "high-risk comments" list was including LOW-severity comments
      alongside a hardcoded "HIGH RISK" badge; now filtered server-side to
      only actually-high-severity comments.
- [x] **Phase 7 — Scheduled collection:** an `APScheduler` background job
      runs all four collectors, in order, every `COLLECTION_INTERVAL_MINUTES`
      (verified directly and via full app startup/registration). **Off by
      default** (`ENABLE_SCHEDULER=false`) — collection stays manual until
      you deliberately opt in, so it can never start burning Apify usage
      unattended just because a token got configured. One platform failing
      logs the error and continues to the next rather than aborting the run.
- [x] **Phase 8 — Relevance filter: short forms:** closed the Phase 4 gap —
      `RELEVANCE_KEYWORDS` now includes common short forms alongside full
      names ("Packages Ltd", "Packages Grp", "Pkgs Mall", "Packages Pak",
      "Packages Conv", etc.), and `relevance.py` normalizes punctuation/
      spacing before matching so hyphenated, underscored, and run-together
      hashtag mentions ("Packages-Mall", "#PackagesMall") match too.
      Deliberately excludes bare 2-3 letter acronyms ("PM", "PG", "PL") —
      verified those false-positive on unrelated chatter ("PM" = Prime
      Minister) far too often to be usable; a full NLP relevance classifier
      (the original spec section 7 suggestion for closing this gap
      precisely) would be the next step if keyword short forms prove
      insufficient. Verified against both new short-form mentions and the
      existing "unrelated packages"/generic "pkgs" negative cases.

See the full product spec for detailed requirements per phase.
