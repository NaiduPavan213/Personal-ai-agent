import os

from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "openai/gpt-4o-mini"
TEMPERATURE = 0

# IANA time zone used for calendar events and "today" (e.g. "Europe/London").
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
