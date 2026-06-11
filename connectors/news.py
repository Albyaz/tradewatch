"""
news.py — fetches news articles for each trade corridor and scores sentiment.
Uses NewsAPI (free tier) + simple keyword-based sentiment scoring.
"""
import logging
import os
from datetime import datetime
import requests
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras

load_dotenv()
log = logging.getLogger(__name__)

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_BASE_URL = "https://newsapi.org/v2/everything"

CORRIDOR_KEYWORDS = {
    "Suez Canal":        "Suez Canal shipping",
    "Panama Canal":      "Panama Canal shipping",
    "Strait of Malacca": "Strait Malacca shipping",
    "Gulf of Aden":      "Gulf Aden Red Sea shipping",
    "Strait of Hormuz":  "Strait Hormuz tanker",
    "English Channel":   "English Channel shipping",
}

NEGATIVE_WORDS = [
    "disruption", "attack", "blocked", "delay", "crisis", "threat",
    "closure", "danger", "piracy", "conflict", "strike", "storm",
    "accident", "collision", "grounded", "detained", "seized", "war",
    "drought", "congestion", "suspended", "halted", "sanctions"
]
POSITIVE_WORDS = [
    "clear", "open", "resumed", "stable", "safe", "improved",
    "normal", "restored", "efficient", "smooth", "resolved"
]

def score_sentiment(text: str) -> float:
    if not text:
        return 0.0
    text_lower = text.lower()
    neg = sum(1 for w in NEGATIVE_WORDS if w in text_lower)
    pos = sum(1 for w in POSITIVE_WORDS if w in text_lower)
    total = neg + pos
    if total == 0:
        return 0.0
    return round((pos - neg) / total, 3)

def fetch_news(corridor: str, query: str) -> list:
    params = {
        "q":        query,
        "sortBy":   "publishedAt",
        "language": "en",
        "pageSize": 10,
        "apiKey":   NEWS_API_KEY,
    }
    resp = requests.get(NEWS_BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    articles = resp.json().get("articles", [])

    rows = []
    for a in articles:
        text = f"{a.get('title', '')} {a.get('description', '')}"
        rows.append({
            "corridor":        corridor,
            "title":           (a.get("title") or "")[:500],
            "description":     (a.get("description") or "")[:1000],
            "source":          (a.get("source", {}).get("name") or "")[:100],
            "url":             (a.get("url") or "")[:500],
            "sentiment_score": score_sentiment(text),
            "published_at":    a.get("publishedAt"),
            "fetched_at":      datetime.utcnow(),
        })
    return rows

def save_news(rows: list) -> int:
    if not rows:
        return 0
    sql = """
        INSERT INTO raw.news_articles (
            corridor, title, description, source, url,
            sentiment_score, published_at, fetched_at
        ) VALUES (
            %(corridor)s, %(title)s, %(description)s, %(source)s, %(url)s,
            %(sentiment_score)s, %(published_at)s, %(fetched_at)s
        )
    """
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    try:
        with conn.cursor() as cur:
            psycopg2.extras.execute_batch(cur, sql, rows, page_size=100)
        conn.commit()
    finally:
        conn.close()
    return len(rows)

def run():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    log.info("=== News connector started ===")
    all_rows = []
    for corridor, query in CORRIDOR_KEYWORDS.items():
        try:
            rows = fetch_news(corridor, query)
            all_rows.extend(rows)
            avg_sentiment = round(sum(r["sentiment_score"] for r in rows) / max(len(rows), 1), 3)
            log.info("%s — %d articles, avg sentiment: %+.3f", corridor, len(rows), avg_sentiment)
        except Exception as e:
            log.error("Failed to fetch news for %s: %s", corridor, e)

    saved = save_news(all_rows)
    log.info("=== Saved %d news articles ===", saved)
    return saved

if __name__ == "__main__":
    run()
