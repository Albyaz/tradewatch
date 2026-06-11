-- TradeWatch Platform — database schema
-- Run once: psql $DATABASE_URL -f db_schema.sql

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

-- Raw vessel positions (AIS data)
CREATE TABLE IF NOT EXISTS raw.vessel_positions (
    id              BIGSERIAL PRIMARY KEY,
    mmsi            TEXT,
    vessel_name     TEXT,
    lat             NUMERIC(9,6),
    lon             NUMERIC(9,6),
    speed           NUMERIC(5,2),
    heading         NUMERIC(5,1),
    corridor        TEXT,
    timestamp       TIMESTAMPTZ,
    fetched_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Raw weather conditions per corridor
CREATE TABLE IF NOT EXISTS raw.corridor_weather (
    id              BIGSERIAL PRIMARY KEY,
    corridor        TEXT NOT NULL,
    lat             NUMERIC(9,6),
    lon             NUMERIC(9,6),
    wind_speed      NUMERIC(6,2),
    wave_height     NUMERIC(5,2),
    visibility      NUMERIC(6,2),
    storm_flag      BOOLEAN DEFAULT FALSE,
    recorded_at     TIMESTAMPTZ,
    fetched_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Raw news articles with sentiment
CREATE TABLE IF NOT EXISTS raw.news_articles (
    id              BIGSERIAL PRIMARY KEY,
    corridor        TEXT NOT NULL,
    title           TEXT,
    description     TEXT,
    source          TEXT,
    url             TEXT,
    sentiment_score NUMERIC(4,3),
    published_at    TIMESTAMPTZ,
    fetched_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Gold mart: daily corridor risk scores
CREATE TABLE IF NOT EXISTS marts.corridor_risk_scores (
    id              BIGSERIAL PRIMARY KEY,
    corridor        TEXT NOT NULL,
    score_date      DATE NOT NULL,
    risk_score      NUMERIC(5,2),
    risk_level      TEXT,
    vessel_count    INTEGER DEFAULT 0,
    avg_wind_speed  NUMERIC(6,2),
    news_sentiment  NUMERIC(4,3),
    predicted_risk  NUMERIC(5,2),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_corridor_date UNIQUE (corridor, score_date)
);

CREATE INDEX IF NOT EXISTS idx_vessel_corridor ON raw.vessel_positions (corridor, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_weather_corridor ON raw.corridor_weather (corridor, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_corridor ON raw.news_articles (corridor, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_risk_corridor ON marts.corridor_risk_scores (corridor, score_date DESC);
