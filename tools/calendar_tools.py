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
    Creates a real Google Calendar event.
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