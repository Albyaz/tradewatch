# 🌍 TradeWatch — Global Trade Risk Intelligence Platform

> A production-grade data engineering platform that monitors the world's most critical shipping corridors in real time, scoring disruption risk daily using live weather, vessel traffic, and geopolitical news sentiment.

**[Live Dashboard →](https://tradewatch-platform.streamlit.app)**

---

## What It Does

TradeWatch ingests data from three sources every 6 hours, transforms it through a medallion architecture, and serves a live risk score (0–100) for each of the world's most critical trade corridors:

| Corridor | Daily Vessel Traffic | Key Risk Factors |
|---|---|---|
| Suez Canal | ~51 vessels/day | Geopolitical tension, sandstorms |
| Panama Canal | ~36 vessels/day | Drought, water levels |
| Strait of Malacca | ~84 vessels/day | Piracy, congestion |
| Gulf of Aden | ~28 vessels/day | Houthi attacks, Red Sea crisis |
| Strait of Hormuz | ~21 vessels/day | Iran tensions, oil tankers |
| English Channel | ~120 vessels/day | Weather, traffic density |

---

## Architecture
Data Sources          Ingestion            Storage           Transformation       Delivery
─────────────         ─────────            ───────           ──────────────       ────────
Open Meteo API   ──► Python connector ──► Neon PostgreSQL ──► dbt staging    ──► Streamlit
NewsAPI          ──► Python connector ──► raw schema      ──► dbt intermediate──► dashboard
AIS Simulator    ──► Python connector ──►                 ──► dbt gold mart  ──► public URL
│
GitHub Actions
(runs every 6h)

**Medallion architecture:**
- **Bronze (raw)** — `raw.vessel_positions`, `raw.corridor_weather`, `raw.news_articles`
- **Silver (staging)** — cleaned, typed, validated dbt views
- **Gold (marts)** — `staging.corridor_risk` — daily risk scores per corridor

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Database | Neon PostgreSQL (serverless) |
| Transformation | dbt Core 1.7 |
| Orchestration | GitHub Actions (cron, every 6h) |
| ML | XGBoost (risk scoring) |
| Dashboard | Streamlit |
| Deployment | Streamlit Cloud |
| Data sources | Open Meteo API, NewsAPI, AIS simulator |

---

## Risk Score Formula

Each corridor receives a daily composite risk score (0–100):
Risk Score = Wind component (0–30)
+ Storm bonus (0–20)
+ News sentiment component (0–25)
+ Vessel density component (0–25)

**Risk levels:**
- 🔴 **CRITICAL** — score ≥ 70
- 🟠 **HIGH** — score ≥ 50
- 🟡 **MEDIUM** — score ≥ 30
- 🟢 **LOW** — score < 30

---

## Project Structure
tradewatch/
├── connectors/
│   ├── weather.py       # Open Meteo API — live weather per corridor
│   ├── news.py          # NewsAPI — articles + sentiment scoring
│   └── vessels.py       # AIS vessel traffic simulator
├── tradewatch_dbt/
│   └── models/
│       ├── staging/     # stg_weather, stg_news, stg_vessels
│       ├── intermediate/# int_corridor_daily (joins all sources)
│       └── marts/       # corridor_risk (final risk scores)
├── dashboard/
│   └── app.py           # Streamlit dashboard
├── .github/
│   └── workflows/
│       └── pipeline.yml # GitHub Actions — runs every 6 hours
├── db_schema.sql        # PostgreSQL schema (raw + staging + marts)
├── run_all.py           # Single entry point for full pipeline run
└── requirements.txt

---

## Running Locally

```bash
# Clone the repo
git clone https://github.com/Albyaz/tradewatch.git
cd tradewatch

# Set up environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Edit .env with your DATABASE_URL and NEWS_API_KEY

# Create database tables
psql $DATABASE_URL -f db_schema.sql

# Run the full pipeline
python run_all.py

# Launch the dashboard
streamlit run dashboard/app.py
```

---

## Data Sources

| Source | Data | Cost |
|---|---|---|
| [Open Meteo](https://open-meteo.com) | Wind speed, gusts, weather codes | Free, no key |
| [NewsAPI](https://newsapi.org) | News articles per corridor | Free tier |
| AIS Simulator | Vessel positions, speed, heading | N/A — realistic simulation |

> **Note on AIS data:** Real-time AIS vessel tracking requires a paid subscription (MarineTraffic, AISHub). This project uses a statistically realistic simulator built on real shipping lane coordinates and historical traffic patterns. The architecture is designed to swap in a live AIS connector with a single file change.

---

## Pipeline Automation

The full pipeline runs automatically every 6 hours via GitHub Actions:

```yaml
on:
  schedule:
    - cron: '0 */6 * * *'
```

Each run:
1. Fetches live weather for all 6 corridors
2. Pulls latest news articles and scores sentiment
3. Simulates vessel traffic
4. Saves all data to Neon PostgreSQL
5. dbt views update automatically on next query

---

## What's Next

- [ ] XGBoost disruption predictor trained on historical crises (Ever Given 2021, Red Sea 2023, Panama drought 2023)
- [ ] Looker Studio public dashboard layer
- [ ] Real AIS data integration (AISHub free tier)
- [ ] Email alert system when corridor crosses risk threshold
- [ ] Historical trend analysis (90-day lookback)

---

## About

Built by **Albright Ndamati** as a production-grade data engineering portfolio project.

Demonstrates end-to-end data engineering: ingestion, transformation, warehousing, orchestration, and visualisation — applied to a real business problem (global supply chain risk monitoring).

**Connect:** [LinkedIn](https://www.linkedin.com/in/albright-ndamati-0a43b4126/) · [GitHub](https://github.com/Albyaz)