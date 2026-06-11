"""
weather.py — fetches real-time weather conditions for all 6 trade corridors
from Open Meteo (free, no API key required).
"""
import logging
import os
from datetime import datetime
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras

load_dotenv()
log = logging.getLogger(__name__)

CORRIDORS = {
    "Suez Canal":          {"lat": 30.5852,  "lon": 32.2654},
    "Panama Canal":        {"lat":  9.0820,  "lon": -79.6813},
    "Strait of Malacca":   {"lat":  2.5000,  "lon": 101.5000},
    "Gulf of Aden":        {"lat": 12.5000,  "lon": 47.5000},
    "Strait of Hormuz":    {"lat": 26.5667,  "lon": 56.2500},
    "English Channel":     {"lat": 50.2000,  "lon":  0.5000},
}

BASE_URL = "https://api.open-meteo.com/v1/forecast"

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_weather(corridor: str, lat: float, lon: float) -> dict:
    params = {
        "latitude":      lat,
        "longitude":     lon,
        "current":       "wind_speed_10m,wind_gusts_10m,weather_code,visibility",
        "forecast_days": 1,
        "timezone":      "UTC",
    }
    resp = requests.get(BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    current      = data.get("current", {})
    wind_speed   = float(current.get("wind_speed_10m") or 0)
    wind_gusts   = float(current.get("wind_gusts_10m") or 0)
    visibility   = min(float(current.get("visibility") or 999), 999.99)  # cap at 999.99
    weather_code = int(current.get("weather_code") or 0)

    wave_height  = round((wind_speed / 20) ** 2, 2)

    storm_flag = (
        wind_speed > 50 or
        wind_gusts > 70 or
        weather_code >= 65
    )

    return {
        "corridor":    corridor,
        "lat":         lat,
        "lon":         lon,
        "wind_speed":  wind_speed,
        "wave_height": wave_height,
        "visibility":  visibility,
        "storm_flag":  storm_flag,
        "recorded_at": datetime.utcnow(),
        "fetched_at":  datetime.utcnow(),
    }

def save_weather(rows: list) -> int:
    if not rows:
        return 0
    sql = """
        INSERT INTO raw.corridor_weather (
            corridor, lat, lon, wind_speed, wave_height,
            visibility, storm_flag, recorded_at, fetched_at
        ) VALUES (
            %(corridor)s, %(lat)s, %(lon)s, %(wind_speed)s, %(wave_height)s,
            %(visibility)s, %(storm_flag)s, %(recorded_at)s, %(fetched_at)s
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
    log.info("=== Weather connector started ===")
    rows = []
    for corridor, coords in CORRIDORS.items():
        try:
            row = fetch_weather(corridor, coords["lat"], coords["lon"])
            rows.append(row)
            storm = "⚠ STORM" if row["storm_flag"] else "✓ clear"
            log.info("%s — wind: %.1f km/h, waves: %.2fm — %s",
                     corridor, row["wind_speed"], row["wave_height"], storm)
        except Exception as e:
            log.error("Failed to fetch weather for %s: %s", corridor, e)

    saved = save_weather(rows)
    log.info("=== Saved %d corridor weather rows ===", saved)
    return saved

if __name__ == "__main__":
    run()
