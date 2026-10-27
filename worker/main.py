"""
Worker Daemon Entrypoint
Polls PostgreSQL for pending jobs at intervals and executes extraction ETL pipeline.
"""

import asyncio
import logging
import sys
from worker.config import worker_settings
from worker.tasks import run_worker_cycle

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WORKER-%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("priceradar.worker")


async def main():
    logger.info("Initializing PriceRadar Background Worker...")
    logger.info("Database URL: %s", worker_settings.async_database_url)
    logger.info("Poll Interval: %ds | Concurrency: %d", worker_settings.WORKER_POLL_INTERVAL_SECONDS, worker_settings.MAX_CONCURRENT_JOBS)

    try:
        while True:
            try:
                processed = await run_worker_cycle()
                if processed > 0:
                    logger.info("Processed %d extraction jobs.", processed)
            except Exception as e:
                logger.warning("Worker cycle encountered an issue (is PostgreSQL running?): %s", e)

            await asyncio.sleep(worker_settings.WORKER_POLL_INTERVAL_SECONDS)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Worker stopped by user request.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
