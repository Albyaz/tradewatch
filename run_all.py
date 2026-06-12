"""
run_all.py — runs the full TradeWatch pipeline.
Called by GitHub Actions every 6 hours.
"""
import logging
import sys
from connectors.weather import run as run_weather
from connectors.news    import run as run_news
from connectors.vessels import run as run_vessels
from ml.risk_model      import predict_today

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

if __name__ == "__main__":
    log.info("========================================")
    log.info("  TradeWatch — full pipeline run")
    log.info("========================================")
    try:
        w = run_weather()
        n = run_news()
        v = run_vessels()
        predict_today()
        log.info("========================================")
        log.info("  Done — weather: %d, news: %d, vessels: %d", w, n, v)
        log.info("========================================")
        sys.exit(0)
    except Exception as e:
        log.exception("Pipeline run failed: %s", e)
        sys.exit(1)
