from langchain_core.tools import tool

from integrations.gmail import (
    send_email,
    list_unread_emails,
)


@tool
def send_email_tool(
    to: str,
    subject: str,
    body: str,
):
    """Send an email using Gmail."""

    message_id = send_email(
        to=to,
        subject=subject,
        body=body,
    )

    return (
        f"Email sent successfully!\n"
        f"Message ID: {message_id}"
    )


@tool
def list_unread_emails_tool(max_results: int = 5):
    """Retrieve and display unread emails from Gmail."""

    return list_unread_emails(max_results=max_results)