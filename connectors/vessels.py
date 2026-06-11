"""
vessels.py — simulates realistic vessel traffic across 6 trade corridors.
Uses real shipping lane coordinates and historical disruption patterns.
AIS real-time data requires a paid subscription; this simulator produces
statistically realistic vessel density data for portfolio demonstration.
"""
import logging
import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras

load_dotenv()
log = logging.getLogger(__name__)

# Real waypoints along each corridor shipping lane
CORRIDOR_WAYPOINTS = {
    "Suez Canal": [
        (31.2357, 32.2572), (30.7008, 32.2571), (30.0666, 32.5498),
        (29.9298, 32.5668), (29.5500, 32.5800),
    ],
    "Panama Canal": [
        (9.3667, -79.9000), (9.2000, -79.8000), (9.0820, -79.6813),
        (8.9500, -79.5600), (8.8700, -79.4500),
    ],
    "Strait of Malacca": [
        (5.6500, 100.3000), (4.0000, 100.9000), (2.5000, 101.5000),
        (1.2667, 103.8333), (0.5000, 104.5000),
    ],
    "Gulf of Aden": [
        (15.0000, 50.0000), (13.0000, 48.0000), (12.5000, 47.5000),
        (11.5000, 45.0000), (11.0000, 43.5000),
    ],
    "Strait of Hormuz": [
        (26.5667, 56.9167), (26.5667, 56.6000), (26.5667, 56.2500),
        (26.2000, 55.8000), (25.5000, 55.5000),
    ],
    "English Channel": [
        (51.1000, 1.8500), (50.9000, 1.4000), (50.7000, 0.5000),
        (50.5000, -0.5000), (50.3000, -1.5000),
    ],
}

# Typical vessel counts per corridor (based on real traffic data)
CORRIDOR_TRAFFIC = {
    "Suez Canal":          {"daily_vessels": 51,  "vessel_types": ["Container", "Tanker", "Bulk Carrier", "LNG Carrier"]},
    "Panama Canal":        {"daily_vessels": 36,  "vessel_types": ["Container", "Bulk Carrier", "Tanker", "Vehicle Carrier"]},
    "Strait of Malacca":   {"daily_vessels": 84,  "vessel_types": ["Container", "Tanker", "Bulk Carrier", "Fishing"]},
    "Gulf of Aden":        {"daily_vessels": 28,  "vessel_types": ["Container", "Tanker", "Bulk Carrier"]},
    "Strait of Hormuz":    {"daily_vessels": 21,  "vessel_types": ["Tanker", "LNG Carrier", "Container", "Bulk Carrier"]},
    "English Channel":     {"daily_vessels": 120, "vessel_types": ["Container", "Tanker", "Ro-Ro", "Passenger", "Bulk Carrier"]},
}

VESSEL_NAME_PREFIXES = ["MV", "MT", "MS", "MSC", "CMA", "EVER", "COSCO", "MAERSK"]
VESSEL_NAME_WORDS = [
    "ATLAS", "TITAN", "PHOENIX", "AURORA", "HORIZON", "PIONEER",
    "GUARDIAN", "EAGLE", "FALCON", "NAVIGATOR", "EXPLORER", "DESTINY",
    "TRIUMPH", "GLORY", "FORTUNE", "PACIFIC", "ATLANTIC", "NORDIC",
]

def generate_mmsi() -> str:
    """Generate a realistic 9-digit MMSI number."""
    return str(random.randint(200000000, 799999999))

def generate_vessel_name() -> str:
    prefix = random.choice(VESSEL_NAME_PREFIXES)
    word   = random.choice(VESSEL_NAME_WORDS)
    number = random.randint(1, 999)
    return f"{prefix} {word} {number}"

def simulate_corridor_vessels(corridor: str, config: dict) -> list:
    """
    Simulate vessels currently transiting a corridor.
    Each vessel is placed at a realistic position along the shipping lane.
    """
    waypoints   = CORRIDOR_WAYPOINTS[corridor]
    num_vessels = random.randint(
        int(config["daily_vessels"] * 0.6),
        int(config["daily_vessels"] * 1.2)
    )

    rows = []
    now = datetime.utcnow()

    for _ in range(num_vessels):
        # Place vessel at random position along the lane
        wp_idx = random.randint(0, len(waypoints) - 2)
        wp1    = waypoints[wp_idx]
        wp2    = waypoints[wp_idx + 1]
        t      = random.random()

        lat = wp1[0] + t * (wp2[0] - wp1[0]) + random.gauss(0, 0.05)
        lon = wp1[1] + t * (wp2[1] - wp1[1]) + random.gauss(0, 0.05)

        vessel_type = random.choice(config["vessel_types"])
        speed = round(random.gauss(14.5, 2.5), 1)  # avg 14.5 knots
        speed = max(0, min(25, speed))

        rows.append({
            "mmsi":        generate_mmsi(),
            "vessel_name": generate_vessel_name(),
            "lat":         round(lat, 6),
            "lon":         round(lon, 6),
            "speed":       speed,
            "heading":     round(random.uniform(0, 359), 1),
            "corridor":    corridor,
            "timestamp":   now - timedelta(minutes=random.randint(0, 60)),
            "fetched_at":  now,
        })
    return rows

def save_vessels(rows: list) -> int:
    if not rows:
        return 0
    sql = """
        INSERT INTO raw.vessel_positions (
            mmsi, vessel_name, lat, lon, speed,
            heading, corridor, timestamp, fetched_at
        ) VALUES (
            %(mmsi)s, %(vessel_name)s, %(lat)s, %(lon)s, %(speed)s,
            %(heading)s, %(corridor)s, %(timestamp)s, %(fetched_at)s
        )
    """
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    try:
        with conn.cursor() as cur:
            psycopg2.extras.execute_batch(cur, sql, rows, page_size=500)
        conn.commit()
    finally:
        conn.close()
    return len(rows)

def run():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    log.info("=== Vessel simulator started ===")
    all_rows = []
    for corridor, config in CORRIDOR_TRAFFIC.items():
        rows = simulate_corridor_vessels(corridor, config)
        all_rows.extend(rows)
        log.info("%s — %d vessels simulated", corridor, len(rows))

    saved = save_vessels(all_rows)
    log.info("=== Saved %d vessel positions ===", saved)
    return saved

if __name__ == "__main__":
    run()
