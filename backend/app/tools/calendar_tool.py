import os
import re
from datetime import datetime, timedelta, timezone
from typing import Optional
from googleapiclient.discovery import build
from app.integrations.google_auth import build_credentials


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_local_timezone():
    """Return a timezone object based on TIMEZONE env var (default Asia/Kolkata / IST)."""
    try:
        from zoneinfo import ZoneInfo
        tz_name = os.environ.get("TIMEZONE", "Asia/Kolkata")
        return ZoneInfo(tz_name)
    except Exception:
        # Fallback: IST = UTC+5:30
        return timezone(timedelta(hours=5, minutes=30))


def _parse_datetime(value: str) -> datetime:
    """
    Accept ISO8601 strings and return a timezone-aware datetime.
    If the string is naive (no tz info), attach the local timezone (IST by default).
    Also catches edge cases where the LLM still passes natural-language strings.
    """
    value = value.strip()
    local_tz = _get_local_timezone()
    now_local = datetime.now(local_tz)

    # ── ISO8601 path ──────────────────────────────────────────────────────────
    if "T" in value:
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                # Naive datetime — assume local timezone, NOT UTC
                dt = dt.replace(tzinfo=local_tz)
            # Safety guard: only fix clearly wrong past years (not legitimate future dates)
            if dt.year < now_local.year - 1:
                dt = dt.replace(year=now_local.year)
            return dt
        except ValueError:
            pass

    # ── Fallback: natural language ────────────────────────────────────────────
    lower = value.lower()

    if "tomorrow" in lower:
        target_date = (now_local + timedelta(days=1)).date()
    elif "yesterday" in lower:
        target_date = (now_local - timedelta(days=1)).date()
    else:
        target_date = now_local.date()

    # Extract time with optional am/pm
    time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', lower)
    hour, minute = 9, 0

    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        meridiem = (time_match.group(3) or "").lower()
        if meridiem == "pm" and hour != 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0
    elif re.match(r'^\d{1,2}$', lower.strip()):
        hour = int(lower.strip())

    return datetime(target_date.year, target_date.month, target_date.day,
                    hour, minute, tzinfo=local_tz)


def get_calendar_service(token_data: dict):
    creds = build_credentials(token_data)
    return build("calendar", "v3", credentials=creds)


# ── list events ───────────────────────────────────────────────────────────────

def list_events(
    token_data: dict,
    max_results: int = 10,
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
) -> dict:
    service = get_calendar_service(token_data)
    local_tz = _get_local_timezone()

    if not time_min:
        time_min = datetime.now(local_tz).isoformat()

    # Ensure time_min is timezone-aware
    try:
        parsed_min = datetime.fromisoformat(time_min)
        if parsed_min.tzinfo is None:
            parsed_min = parsed_min.replace(tzinfo=local_tz)
        time_min = parsed_min.isoformat()
    except Exception:
        time_min = datetime.now(local_tz).isoformat()

    kwargs: dict = dict(
        calendarId="primary",
        timeMin=time_min,
        maxResults=max_results,
        singleEvents=True,
        orderBy="startTime",
    )

    if time_max:
        try:
            parsed_max = datetime.fromisoformat(time_max)
            if parsed_max.tzinfo is None:
                parsed_max = parsed_max.replace(tzinfo=local_tz)
            kwargs["timeMax"] = parsed_max.isoformat()
        except Exception:
            pass  # ignore bad time_max rather than crashing

    events_result = service.events().list(**kwargs).execute()

    return {
        "events": [
            {
                "id": e.get("id"),
                "summary": e.get("summary", "No title"),
                "start": e.get("start", {}),
                "end": e.get("end", {}),
                "description": e.get("description", ""),
                "htmlLink": e.get("htmlLink", ""),
            }
            for e in events_result.get("items", [])
        ]
    }


# ── create event ──────────────────────────────────────────────────────────────

def create_event(
    token_data: dict,
    summary: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
    add_meet: bool = False,
    attendees: Optional[list] = None,
) -> dict:
    service = get_calendar_service(token_data)

    start_dt = _parse_datetime(start_time)
    try:
        end_dt = _parse_datetime(end_time)
        if end_dt <= start_dt:
            end_dt = start_dt + timedelta(hours=1)
    except Exception:
        end_dt = start_dt + timedelta(hours=1)

    print(f"[CALENDAR] Creating event '{summary}': {start_dt.isoformat()} → {end_dt.isoformat()}")

    event_body = {
        "summary": summary,
        "description": description,
        "location": location,
        "start": {"dateTime": start_dt.isoformat()},
        "end":   {"dateTime": end_dt.isoformat()},
    }

    if attendees:
        event_body["attendees"] = [{"email": email.strip()} for email in attendees]

    if add_meet:
        event_body["conferenceData"] = {
            "createRequest": {"requestId": f"meet-{datetime.now().timestamp()}"}
        }

    result = service.events().insert(
        calendarId="primary",
        body=event_body,
        conferenceDataVersion=1 if add_meet else 0,
        sendUpdates="all",
    ).execute()

    return {
        "id": result.get("id"),
        "summary": result.get("summary"),
        "htmlLink": result.get("htmlLink"),
        "meetLink": result.get("conferenceData", {})
                        .get("entryPoints", [{}])[0].get("uri"),
        "start": result.get("start"),
        "end": result.get("end"),
        "attendees": result.get("attendees"),
    }


# ── delete event ──────────────────────────────────────────────────────────────

def delete_event(token_data: dict, event_id: str) -> dict:
    service = get_calendar_service(token_data)
    service.events().delete(calendarId="primary", eventId=event_id).execute()
    return {"deleted": True, "event_id": event_id}


# ── delete event (already defined above, this is the public wrapper) ──────────

def delete_event(token_data: dict, event_id: str) -> dict:
    """Delete a Google Calendar event by ID."""
    service = get_calendar_service(token_data)
    try:
        service.events().delete(calendarId="primary", eventId=event_id).execute()
        return {"deleted": True, "event_id": event_id}
    except Exception as e:
        return {"deleted": False, "event_id": event_id, "error": str(e)}


def list_events_for_day(token_data: dict, date_str: str) -> dict:
    """List all events on a specific date (YYYY-MM-DD). Used for 'delete all today's events'."""
    local_tz = _get_local_timezone()
    from datetime import date
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=local_tz)
    except ValueError:
        d = datetime.now(local_tz)

    day_start = d.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = d.replace(hour=23, minute=59, second=59, microsecond=0)

    return list_events(
        token_data,
        max_results=50,
        time_min=day_start.isoformat(),
    )
