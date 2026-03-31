"""
Morning brief scheduler for IndiaFish Telegram delivery.
"""

import logging
import threading
import time
from datetime import datetime

import pytz
import schedule

from app.config import Config
from app.services.fo_signal_generator import process_simulation_output
from app.services.scenario_runner import run_simulation
from app.services.telegram_bot import send_message, send_report


logger = logging.getLogger(__name__)


def run_morning_brief() -> None:
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    logger.info("Running morning brief at %s", now.isoformat())

    scenario_id = "weekly_expiry_thursday" if now.weekday() == 3 else "custom"
    custom_var = None
    if scenario_id == "custom":
        custom_var = (
            f"Today is {now.strftime('%A %d %B %Y')}. "
            "Analyse current Nifty F&O market conditions based on the seed data. "
            "What is the likely market direction today and key levels to watch?"
        )

    result = run_simulation(
        scenario_id,
        n_agents=200,
        n_rounds=20,
        custom_variable=custom_var,
        use_mock_seed=(Config.SEED_MODE == "mock"),
    )
    processed = process_simulation_output(result)

    recipients = []
    if Config.TELEGRAM_ADMIN_CHAT_ID:
        recipients.append(str(Config.TELEGRAM_ADMIN_CHAT_ID))
    recipients.extend(str(chat_id) for chat_id in Config.TELEGRAM_ALLOWED_USERS)

    seen = set()
    for chat_id in recipients:
        if not chat_id or chat_id in seen:
            continue
        seen.add(chat_id)
        try:
            send_report(chat_id, processed)
            time.sleep(0.5)
        except Exception as exc:
            logger.error("Failed to send morning brief to %s: %s", chat_id, exc)
            send_message(chat_id, "Morning brief generation failed.")


def start_scheduler() -> threading.Thread:
    def run():
        schedule.every().day.at("03:15").do(run_morning_brief)
        while True:
            schedule.run_pending()
            time.sleep(30)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread
