
from langchain.agents import create_agent

from utils.llm import llm
from tools.calendar_tools import (
    create_calendar_event,
    list_calendar_events,
)
from prompts.calendar_prompt import CALENDAR_PROMPT

calendar_agent = create_agent(
    model=llm,
    tools=[
        create_calendar_event,
        list_calendar_events,
    ],
    system_prompt=CALENDAR_PROMPT,
)
