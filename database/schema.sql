-- Packages Group Monitor — core schema (section 17 of the product spec)
-- Run against PostgreSQL (Supabase or otherwise). Idempotent via IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS comments (
    id              BIGSERIAL PRIMARY KEY,
    platform        VARCHAR(20) NOT NULL,          -- linkedin | reddit | facebook | instagram
    source_type     VARCHAR(20) NOT NULL,          -- post | comment | reply
    post_id         VARCHAR(255),
    comment_id      VARCHAR(255),
    post_url        TEXT,
    comment_url     TEXT,
    text            TEXT NOT NULL,
    author_name     VARCHAR(255),
    created_at      TIMESTAMPTZ,
    engagement      INTEGER NOT NULL DEFAULT 0,
    collected_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_relevant     BOOLEAN,
    dedup_key       VARCHAR(64) NOT NULL UNIQUE    -- app-computed hash of platform + comment/post id
);

CREATE INDEX IF NOT EXISTS idx_comments_platform     ON comments(platform);
CREATE INDEX IF NOT EXISTS idx_comments_created_at   ON comments(created_at);
CREATE INDEX IF NOT EXISTS idx_comments_is_relevant  ON comments(is_relevant);

CREATE TABLE IF NOT EXISTS sentiment_analysis (
    id              BIGSERIAL PRIMARY KEY,
    comment_id      BIGINT NOT NULL UNIQUE REFERENCES comments(id) ON DELETE CASCADE,
    sentiment       VARCHAR(10) NOT NULL,          -- positive | neutral | negative | mixed
    confidence      NUMERIC(5,4) NOT NULL,
    severity        SMALLINT,                      -- 0-100, only meaningful for negative/mixed
    topic           VARCHAR(50),
    analyzed_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sentiment_sentiment ON sentiment_analysis(sentiment);
CREATE INDEX IF NOT EXISTS idx_sentiment_topic     ON sentiment_analysis(topic);
CREATE INDEX IF NOT EXISTS idx_sentiment_severity  ON sentiment_analysis(severity);

CREATE TABLE IF NOT EXISTS collection_runs (
    id                  BIGSERIAL PRIMARY KEY,
    platform            VARCHAR(20) NOT NULL,
    started_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at        TIMESTAMPTZ,
    items_collected     INTEGER NOT NULL DEFAULT 0,
    items_new           INTEGER NOT NULL DEFAULT 0,
    items_duplicate     INTEGER NOT NULL DEFAULT 0,
    status              VARCHAR(20) NOT NULL DEFAULT 'running', -- running | success | failed
    error_message       TEXT
);

CREATE INDEX IF NOT EXISTS idx_collection_runs_platform ON collection_runs(platform);

CREATE TABLE IF NOT EXISTS alerts (
    id              BIGSERIAL PRIMARY KEY,
    comment_id      BIGINT REFERENCES comments(id) ON DELETE CASCADE,
    alert_type      VARCHAR(30) NOT NULL,   -- high_severity | critical | negative_spike | topic_spike | mention_spike
    severity        VARCHAR(10),
    message         TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_resolved     BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX IF NOT EXISTS idx_alerts_is_resolved ON alerts(is_resolved);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at  ON alerts(created_at);
