"""
Google Calendar → Telegram Notification Agent
============================================
Polls Google Calendar and sends cute motivational Telegram messages
for upcoming events.

Notification schedule per event:
  • Morning digest  → sent once at 8:00 AM listing all events for the day
  • 30-min reminder → sent when event is ~30 minutes away
  • 10-min reminder → sent when event is ~10 minutes away
  • Start alert     → sent when event is starting now (within 1 min)
"""

import os
import time
import logging
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

from calendar_service import get_calendar_service, get_upcoming_events, get_todays_events
from telegram_service import send_message, test_connection
from messages import get_reminder_message, get_starting_now_message, get_morning_message

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
load_dotenv()

POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))   # how often to poll
REMINDER_MINUTES_AHEAD = int(os.getenv("REMINDER_MINUTES_AHEAD", "30")) # first reminder window
CLOSE_REMINDER_MINUTES = int(os.getenv("CLOSE_REMINDER_MINUTES", "10")) # second reminder window
CALENDAR_ID = os.getenv("CALENDAR_ID", "primary")
MORNING_DIGEST_HOUR = int(os.getenv("MORNING_DIGEST_HOUR", "8"))         # 24-h local hour

# ── State tracking (in-memory; resets on restart) ─────────────────────────────
# Keys: "{event_id}:{notification_type}"
# Values: True once a notification has been sent
sent_notifications: set[str] = set()
morning_digest_sent_date: str = ""  # "YYYY-MM-DD"


def notification_key(event_id: str, ntype: str) -> str:
    return f"{event_id}:{ntype}"


def already_sent(event_id: str, ntype: str) -> bool:
    return notification_key(event_id, ntype) in sent_notifications


def mark_sent(event_id: str, ntype: str) -> None:
    sent_notifications.add(notification_key(event_id, ntype))


def send_morning_digest(service) -> None:
    """Send a digest of all today's events at the configured morning hour."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    global morning_digest_sent_date

    if morning_digest_sent_date == today_str:
        return  # already sent today

    now_hour = datetime.now().hour
    if now_hour < MORNING_DIGEST_HOUR:
        return  # not yet morning

    events = get_todays_events(service, calendar_id=CALENDAR_ID)

    if not events:
        msg = (
            "Good morning, sunshine! ☀️\n"
            "No events on your calendar today — enjoy your free day! 🌸✨"
        )
    else:
        lines = ["Good morning, bestie!! ☀️🎀 Here's what's on your plate today:\n"]
        for ev in events:
            lines.append(f"  📌 *{ev['title']}* — {ev['start_str']}")
        lines.append("\nYou're going to absolutely slay today, I know it!! 💪💖")
        msg = "\n".join(lines)

    if send_message(msg):
        morning_digest_sent_date = today_str
        logger.info("Morning digest sent.")


def check_and_notify(service) -> None:
    """
    Fetch events in the next REMINDER_MINUTES_AHEAD + 5 minutes
    and fire the appropriate notifications.
    """
    now = datetime.now(timezone.utc)
    window = REMINDER_MINUTES_AHEAD + 5  # fetch a slightly wider window

    events = get_upcoming_events(service, minutes_ahead=window, calendar_id=CALENDAR_ID)

    for ev in events:
        event_id = ev["id"]
        title = ev["title"]
        start_dt = ev["start_dt"]
        start_str = ev["start_str"]

        minutes_until = (start_dt - now).total_seconds() / 60

        # ── Starting now (within 1 minute) ───────────────────────────────────
        if 0 <= minutes_until < 1:
            if not already_sent(event_id, "start"):
                msg = get_starting_now_message(title)
                if send_message(msg):
                    mark_sent(event_id, "start")

        # ── 10-minute reminder ────────────────────────────────────────────────
        elif CLOSE_REMINDER_MINUTES - 1 <= minutes_until < CLOSE_REMINDER_MINUTES + 1:
            if not already_sent(event_id, "10min"):
                msg = get_reminder_message(title, start_str)
                if send_message(f"⏰ *10-minute heads-up!*\n\n{msg}"):
                    mark_sent(event_id, "10min")

        # ── 30-minute reminder ────────────────────────────────────────────────
        elif REMINDER_MINUTES_AHEAD - 2 <= minutes_until < REMINDER_MINUTES_AHEAD + 2:
            if not already_sent(event_id, "30min"):
                msg = get_reminder_message(title, start_str)
                if send_message(msg):
                    mark_sent(event_id, "30min")


def run() -> None:
    logger.info("🤖  Google Calendar → Telegram Agent starting up...")

    # Verify Telegram
    if not test_connection():
        logger.error("Telegram connection failed. Check TELEGRAM_BOT_TOKEN.")
        return

    # Build Calendar service
    try:
        service = get_calendar_service()
        logger.info("Google Calendar service ready.")
    except Exception as e:
        logger.error(f"Could not initialise Google Calendar service: {e}")
        return

    # Startup message
    send_message(
        "🤖✨ Hey girly! Your calendar assistant is ONLINE!\n"
        "I'll ping you before every event so you never miss a thing 💖📅"
    )

    logger.info(
        f"Polling every {POLL_INTERVAL_SECONDS}s | "
        f"Reminders at {REMINDER_MINUTES_AHEAD}min & {CLOSE_REMINDER_MINUTES}min before events"
    )

    while True:
        try:
            send_morning_digest(service)
            check_and_notify(service)
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    run()
