from datetime import datetime
from zoneinfo import ZoneInfo

from langchain.agents import create_agent

from config import TIMEZONE

from utils.llm import llm
from agents.calendar_agent import calendar_agent
from agents.email_agent import email_agent
from agents.image_agent import answer_about_image
from langchain_core.tools import tool
from prompts.supervisor_prompt import SUPERVISOR_PROMPT

def with_current_time(query: str) -> str:
    """Prefix a query with the current date/time so agents can resolve
    relative dates like "tomorrow" or "next Friday"."""

    now = datetime.now(ZoneInfo(TIMEZONE))
    return (
        f"Current date and time: {now:%A, %Y-%m-%d %H:%M} ({TIMEZONE}).\n\n"
        f"{query}"
    )


@tool(return_direct=True)
def calendar_assistant(query: str) -> str:
    """Delegate calendar-related tasks to the Calendar Agent."""

    response = calendar_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": with_current_time(query)
                }
            ]
        }
    )

    return response["messages"][-1].content


@tool(return_direct=True)
def email_assistant(query: str) -> str:
    """Delegate email-related tasks to the Email Agent."""

    response = email_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": with_current_time(query)
                }
            ]
        }
    )

    return response["messages"][-1].content


@tool(return_direct=True)
def image_assistant(question: str) -> str:
    """
    Answer questions about the image the user attached: describe it,
    read text in it, identify things in it, and so on.
    """

    return answer_about_image(question)


supervisor = create_agent(
    model=llm,
    tools=[
        calendar_assistant,
        email_assistant,
        image_assistant,
    ],
    system_prompt=SUPERVISOR_PROMPT
)