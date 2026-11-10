from datetime import datetime, timedelta, timezone

from googleapiclient.discovery import build

from config import TIMEZONE
from integrations.auth import authenticate_google


def create_google_calendar_event(
    title: str,
    date: str,
    time: str,
):
    """
    Creates an event in Google Calendar.
    """

    creds = authenticate_google()

    service = build(
        "calendar",
        "v3",
        credentials=creds,
    )

    # Convert strings into datetime (date: YYYY-MM-DD, time: HH:MM 24-hour)
    start = datetime.strptime(
        f"{date} {time}",
        "%Y-%m-%d %H:%M"
    )

    # timedelta handles events that cross midnight (e.g. 23:30)
    end = start + timedelta(hours=1)

    event = {
        "summary": title,
        "start": {
            "dateTime": start.isoformat(),
            "timeZone": TIMEZONE,
        },
        "end": {
            "dateTime": end.isoformat(),
            "timeZone": TIMEZONE,
        },
    }

    event = (
        service.events()
        .insert(
            calendarId="primary",
            body=event,
        )
        .execute()
    )

    return event["htmlLink"]





def list_upcoming_events(max_results=10):
    """
    Returns the next upcoming calendar events.
    """

    creds = authenticate_google()

    service = build(
        "calendar",
        "v3",
        credentials=creds,
    )

    now = datetime.now(timezone.utc).isoformat()

    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    events = events_result.get("items", [])

    if not events:
        return "No upcoming events found."

    output = []

    for event in events:

        start = event["start"].get(
            "dateTime",
            event["start"].get("date")
        )

        title = event.get("summary", "No Title")

        output.append(
            f"{title}\n{start}"
        )

    return "\n\n".join(output)