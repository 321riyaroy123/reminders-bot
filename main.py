"""
Google Calendar → Telegram Notification Agent
============================================
Runs as a Render FREE-tier Web Service.

  • Flask serves GET / (health check) so Render keeps the container alive
  • The calendar polling loop runs in a background daemon thread
  • Pin UptimeRobot (free) to your Render URL every 5 min so the
    dyno never idles/spins down
"""

import os
import time
import logging
import threading
from datetime import datetime, timezone

from flask import Flask, jsonify
from dotenv import load_dotenv

from calendar_service import get_calendar_service, get_upcoming_events, get_todays_events
from telegram_service import send_message, test_connection
from messages import get_reminder_message, get_starting_now_message, get_morning_message

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
load_dotenv()

POLL_INTERVAL_SECONDS  = int(os.getenv("POLL_INTERVAL_SECONDS",  "60"))
REMINDER_MINUTES_AHEAD = int(os.getenv("REMINDER_MINUTES_AHEAD", "30"))
CLOSE_REMINDER_MINUTES = int(os.getenv("CLOSE_REMINDER_MINUTES", "10"))
CALENDAR_ID            = os.getenv("CALENDAR_ID", "primary")
MORNING_DIGEST_HOUR    = int(os.getenv("MORNING_DIGEST_HOUR", "8"))
PORT                   = int(os.getenv("PORT", "8080"))   # Render injects PORT

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)

# Shared state exposed to the health endpoint
agent_state = {
    "status": "starting",
    "last_poll": None,
    "events_checked": 0,
    "notifications_sent": 0,
    "errors": 0,
}


@app.route("/")
def health():
    return jsonify({
        "ok": True,
        "agent": agent_state,
    })


@app.route("/ping")
def ping():
    """Lightweight endpoint for UptimeRobot pings."""
    return "pong", 200


# ── Agent state ───────────────────────────────────────────────────────────────
sent_notifications: set = set()
morning_digest_sent_date: str = ""


def already_sent(event_id: str, ntype: str) -> bool:
    return f"{event_id}:{ntype}" in sent_notifications


def mark_sent(event_id: str, ntype: str) -> None:
    sent_notifications.add(f"{event_id}:{ntype}")


def send_morning_digest(service) -> None:
    global morning_digest_sent_date
    today_str = datetime.now().strftime("%Y-%m-%d")

    if morning_digest_sent_date == today_str:
        return
    if datetime.now().hour < MORNING_DIGEST_HOUR:
        return

    events = get_todays_events(service, calendar_id=CALENDAR_ID)

    if not events:
        msg = (
            "Good morning, sunshine! ☀️\n"
            "No events today — enjoy your free day! 🌸✨"
        )
    else:
        lines = ["Good morning, bestie!! ☀️🎀 Here's your day:\n"]
        for ev in events:
            lines.append(f"  📌 *{ev['title']}* — {ev['start_str']}")
        lines.append("\nYou're going to absolutely slay today!! 💪💖")
        msg = "\n".join(lines)

    if send_message(msg):
        morning_digest_sent_date = today_str
        agent_state["notifications_sent"] += 1
        logger.info("Morning digest sent.")


def check_and_notify(service) -> None:
    now = datetime.now(timezone.utc)
    window = REMINDER_MINUTES_AHEAD + 5

    events = get_upcoming_events(service, minutes_ahead=window, calendar_id=CALENDAR_ID)
    agent_state["events_checked"] += len(events)

    for ev in events:
        event_id  = ev["id"]
        title     = ev["title"]
        start_dt  = ev["start_dt"]
        start_str = ev["start_str"]

        minutes_until = (start_dt - now).total_seconds() / 60

        # Starting NOW (within 1 minute)
        if 0 <= minutes_until < 1:
            if not already_sent(event_id, "start"):
                msg = get_starting_now_message(title)
                if send_message(msg):
                    mark_sent(event_id, "start")
                    agent_state["notifications_sent"] += 1

        # 10-minute reminder
        elif CLOSE_REMINDER_MINUTES - 1 <= minutes_until < CLOSE_REMINDER_MINUTES + 1:
            if not already_sent(event_id, "10min"):
                msg = get_reminder_message(title, start_str)
                if send_message(f"⏰ *10-minute heads-up!*\n\n{msg}"):
                    mark_sent(event_id, "10min")
                    agent_state["notifications_sent"] += 1

        # 30-minute reminder
        elif REMINDER_MINUTES_AHEAD - 2 <= minutes_until < REMINDER_MINUTES_AHEAD + 2:
            if not already_sent(event_id, "30min"):
                msg = get_reminder_message(title, start_str)
                if send_message(msg):
                    mark_sent(event_id, "30min")
                    agent_state["notifications_sent"] += 1


# ── Background polling thread ─────────────────────────────────────────────────
def agent_loop():
    logger.info("Agent loop starting…")

    if not test_connection():
        logger.error("Telegram connection failed. Check TELEGRAM_BOT_TOKEN.")
        agent_state["status"] = "telegram_error"
        return

    try:
        service = get_calendar_service()
        logger.info("Google Calendar service ready.")
    except Exception as e:
        logger.error(f"Could not initialise Google Calendar service: {e}")
        agent_state["status"] = "calendar_error"
        return

    send_message(
        "🤖✨ Hey girly! Your calendar assistant is ONLINE!\n"
        "I'll ping you before every event so you never miss a thing 💖📅"
    )
    agent_state["status"] = "running"

    while True:
        try:
            send_morning_digest(service)
            check_and_notify(service)
            agent_state["last_poll"] = datetime.now().isoformat()
        except Exception as e:
            logger.error(f"Error in agent loop: {e}", exc_info=True)
            agent_state["errors"] += 1

        time.sleep(POLL_INTERVAL_SECONDS)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Start the agent in a background daemon thread
    t = threading.Thread(target=agent_loop, daemon=True)
    t.start()

    # Start Flask — Render requires a web server listening on PORT
    logger.info(f"Flask web server listening on port {PORT}")
    app.run(host="0.0.0.0", port=PORT)
