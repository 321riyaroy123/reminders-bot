import os
import json
import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def get_calendar_service():
    """
    Build and return a Google Calendar API service.
    Supports two auth modes (set via AUTH_MODE env var):
      - "service_account" (default for Render): uses GOOGLE_SERVICE_ACCOUNT_JSON env var
      - "oauth": uses token.pickle or OAuth flow
    """
    auth_mode = os.getenv("AUTH_MODE", "service_account").lower()

    if auth_mode == "service_account":
        sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not sa_json:
            raise ValueError(
                "GOOGLE_SERVICE_ACCOUNT_JSON env var is required for service_account auth mode."
            )
        # Support both raw JSON string and base64-encoded JSON
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
        raise ValueError(f"Unknown AUTH_MODE: {auth_mode}. Use 'service_account' or 'oauth'.")

    service = build("calendar", "v3", credentials=creds)
    return service


def get_upcoming_events(service, minutes_ahead: int = 60, calendar_id: str = "primary") -> List[Dict]:
    """
    Fetch events starting within the next `minutes_ahead` minutes.
    Returns a list of event dicts with keys: id, title, start_dt, start_str
    """
    now = datetime.now(timezone.utc)
    time_min = now.isoformat()
    time_max = (now + timedelta(minutes=minutes_ahead)).isoformat()

    try:
        events_result = (
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
        raw_events = events_result.get("items", [])
    except Exception as e:
        logger.error(f"Failed to fetch events: {e}")
        return []

    events = []
    for ev in raw_events:
        start = ev.get("start", {})
        start_str = start.get("dateTime") or start.get("date")
        if not start_str:
            continue

        # Parse to datetime
        try:
            if "T" in start_str:
                start_dt = datetime.fromisoformat(start_str)
                # Ensure timezone-aware
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=timezone.utc)
            else:
                # All-day event — treat start as midnight UTC
                d = datetime.strptime(start_str, "%Y-%m-%d")
                start_dt = d.replace(tzinfo=timezone.utc)
        except ValueError:
            logger.warning(f"Could not parse event start time: {start_str}")
            continue

        events.append(
            {
                "id": ev.get("id"),
                "title": ev.get("summary", "Untitled Event"),
                "start_dt": start_dt,
                "start_str": start_dt.strftime("%I:%M %p"),
            }
        )

    return events


def get_todays_events(service, calendar_id: str = "primary") -> List[Dict]:
    """Fetch all events for today (used for morning digest)."""
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()

    try:
        events_result = (
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
        raw_events = events_result.get("items", [])
    except Exception as e:
        logger.error(f"Failed to fetch today's events: {e}")
        return []

    events = []
    for ev in raw_events:
        start = ev.get("start", {})
        start_str = start.get("dateTime") or start.get("date")
        if not start_str:
            continue
        try:
            if "T" in start_str:
                start_dt = datetime.fromisoformat(start_str)
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=timezone.utc)
                time_label = start_dt.strftime("%I:%M %p")
            else:
                time_label = "All day"
                start_dt = None
        except ValueError:
            time_label = start_str
            start_dt = None

        events.append(
            {
                "id": ev.get("id"),
                "title": ev.get("summary", "Untitled Event"),
                "start_dt": start_dt,
                "start_str": time_label,
            }
        )

    return events
