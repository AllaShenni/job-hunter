import logging
import traceback
from apscheduler.schedulers.blocking import BlockingScheduler
from zoneinfo import ZoneInfo

from config import SCHEDULE_HOURS, TIMEZONE, SUPERJOB_API_KEY
from searcher_hh_rss import fetch_hh_vacancies
from searcher_superjob import fetch_superjob_vacancies
from scraper_tg import fetch_telegram_vacancies
from notifier import send_report, send_error, redact

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
# Silence noisy HTTP loggers — they dump full URLs (with bot tokens) at INFO level.
# Token in URL must never appear in stdout/logs.
for noisy in ("httpx", "httpcore", "telethon", "telethon.network", "telethon.client"):
    logging.getLogger(noisy).setLevel(logging.WARNING)
log = logging.getLogger(__name__)


def run_search() -> None:
    log.info("Starting vacancy search…")
    all_vacancies = []

    sources = [
        ("hh.ru", fetch_hh_vacancies),
        ("Telegram channels", fetch_telegram_vacancies),
    ]
    # SuperJob needs a free app key (api.superjob.ru) in the SUPERJOB_API_KEY secret.
    if SUPERJOB_API_KEY:
        sources.append(("SuperJob", fetch_superjob_vacancies))

    for name, fetcher in sources:
        try:
            found = fetcher()
            log.info(f"{name}: {len(found)} new vacancies")
            all_vacancies.extend(found)
        except Exception as exc:
            log.error(f"{name} failed: {redact(str(exc))}")
            send_error(f"{name}: {traceback.format_exc()}")

    log.info(f"Total new vacancies: {len(all_vacancies)}")
    send_report(all_vacancies)


def main() -> None:
    tz = ZoneInfo(TIMEZONE)
    scheduler = BlockingScheduler(timezone=tz)

    for hour in SCHEDULE_HOURS:
        scheduler.add_job(run_search, "cron", hour=hour, minute=0)
        log.info(f"Scheduled search at {hour:02d}:00 {TIMEZONE}")

    log.info("Job Hunter Bot started. Waiting for scheduled runs…")
    scheduler.start()


if __name__ == "__main__":
    main()
