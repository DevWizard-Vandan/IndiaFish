import logging
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.services.morning_scheduler import start_scheduler
from app.services.telegram_bot import start_bot_thread


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)


app = create_app()


with app.app_context():
    logging.info("Starting morning brief scheduler...")
    start_scheduler()

    logging.info("Starting Telegram bot...")
    logging.info("Send /start to your bot to test.")
    start_bot_thread()

    while True:
        time.sleep(60)
