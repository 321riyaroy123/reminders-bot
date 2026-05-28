import os
import json
import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def get_calendar_service():
    auth_mode = os.getenv("AUTH_MODE", "service_account").lower()

    if auth_mode == "service_account":
        sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not sa_json:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON env var is required.")
        try:
            info = json.loads(sa_json)
        except json.JSONDecodeError:
            info = json.loads(base64.b64decode(sa_json).decode("utf-8"))

        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        logger.info("Authenticated via Service Account.")

    elif auth_mode == "oauth":
        creds = None
        token_path = "token.pickle"
        if os.path.exists(token_path):
            with open(token_path, "rb") as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, "wb") as token:
                pickle.dump(creds, token)
        logger.info("Authenticated via OAuth.")
    else:
        raise ValueError(f"Unknown AUTH_MODE: {auth_mode}")

    service = build("calendar", "v3", credentials=creds)
    return service


def _parse_event(ev: dict) -> dict | None:
    """Parse a raw Google Calendar event dict into a clean dict. Returns None if unparseable."""
    start = ev.get("start", {})
    raw = start.get("dateTime") or start.get("date")
    if not raw:
        return None
    try:
        if "T" in raw:
            start_dt = datetime.fromisoformat(raw)
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)
            time_label = start_dt.strftime("%I:%M %p")
        else:
            d = datetime.strptime(raw, "%Y-%m-%d")
            start_dt = d.replace(tzinfo=timezone.utc)
            time_label = "All day"
    except ValueError:
        logger.warning(f"Could not parse event time: {raw}")
        return None

    return {
        "id": ev.get("id"),
        "title": ev.get("summary", "Untitled Event"),
        "start_dt": start_dt,
        "start_str": time_label,
    }


def get_upcoming_events(service, minutes_ahead: int = 60, calendar_id: str = "primary") -> List[Dict]:
    """
    Fetch events whose start time falls within the next `minutes_ahead` minutes.
    BUG FIX: Use timeMin = now - 2min so events that started very recently
    (within the poll window) are still caught.
    """
    now = datetime.now(timezone.utc)
    # Look back 2 min so we don't miss events due to polling jitter
    time_min = (now - timedelta(minutes=2)).isoformat()
    time_max = (now + timedelta(minutes=minutes_ahead)).isoformat()

    try:
        result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
    except Exception as e:
        logger.error(f"Failed to fetch upcoming events: {e}")
        return []

    events = []
    for ev in result.get("items", []):
        parsed = _parse_event(ev)
        if parsed:
            events.append(parsed)
    return events


def get_todays_events(service, calendar_id: str = "primary") -> List[Dict]:
    """Fetch all events for today (UTC date)."""
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    end_of_day   = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()

    try:
        result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=start_of_day,
                timeMax=end_of_day,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
    except Exception as e:
        logger.error(f"Failed to fetch today's events: {e}")
        return []

    events = []
    for ev in result.get("items", []):
        parsed = _parse_event(ev)
        if parsed:
            events.append(parsed)
    return events
