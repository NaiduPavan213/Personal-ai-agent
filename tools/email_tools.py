from langchain_core.tools import tool

from integrations.gmail import list_unread_emails
from utils.email_confirmation import save_draft


@tool
def draft_email_tool(
    to: str,
    subject: str,
    body: str,
):
    """
    Prepare an email for the user to review.

    This does NOT send the email. The draft is shown to the user, and it is
    sent only if the user confirms it.
    """

    save_draft(to=to, subject=subject, body=body)

    return (
        "Draft saved. It will be shown to the user, who must confirm it "
        "before it is sent. The email has NOT been sent."
    )


@tool
def list_unread_emails_tool(max_results: int = 5):
    """Retrieve and display unread emails from Gmail."""

    return list_unread_emails(max_results=max_results)
