"""
run_all.py — runs all three connectors in sequence.
This is what GitHub Actions will call on a schedule.
"""
import logging
import sys
from connectors.weather import run as run_weather
from connectors.news    import run as run_news
from connectors.vessels import run as run_vessels

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
        log.info("========================================")
        log.info("  Done — weather: %d, news: %d, vessels: %d", w, n, v)
        log.info("========================================")
        sys.exit(0)
    except Exception as e:
        log.exception("Pipeline run failed: %s", e)
        sys.exit(1)
