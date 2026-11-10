from langchain_core.tools import tool

from integrations.google_calendar import create_google_calendar_event
from integrations.google_calendar import list_upcoming_events

@tool
def create_calendar_event(
    title: str,
    date: str,
    time: str,
):
    """
    Creates a real one-hour Google Calendar event.

    Args:
        title: Event title.
        date: Event date in YYYY-MM-DD format (e.g. 2026-11-11).
        time: Start time in 24-hour HH:MM format (e.g. 15:00 for 3 PM).
    """

    link = create_google_calendar_event(
        title,
        date,
        time,
    )

    return (
        f"✅ Calendar event created successfully!\n\n"
        f"View it here:\n{link}"
    )




@tool
def list_calendar_events():
    """
    List upcoming calendar events.
    """

    return list_upcoming_events()