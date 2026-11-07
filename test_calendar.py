from integrations.google_calendar import create_google_calendar_event

link = create_google_calendar_event(
    title="LangChain Meeting",
    date="2026-07-25",
    time="21:00",
)

print(link)