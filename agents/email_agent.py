from langchain.agents import create_agent

from utils.llm import llm

from tools.email_tools import (
    draft_email_tool,
    list_unread_emails_tool,
)

from prompts.email_prompt import EMAIL_PROMPT


email_agent = create_agent(
    model=llm,
    tools=[
        draft_email_tool,
        list_unread_emails_tool,
    ],
    system_prompt=EMAIL_PROMPT,
)