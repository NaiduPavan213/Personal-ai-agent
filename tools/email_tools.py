from langchain_core.tools import tool

from integrations.gmail import list_unread_emails
from utils.attachments import get_image
from utils.email_confirmation import save_draft


@tool
def draft_email_tool(
    to: str,
    subject: str,
    body: str,
    attach_image: bool = False,
):
    """
    Prepare an email for the user to review.

    This does NOT send the email. The draft is shown to the user, and it is
    sent only if the user confirms it.

    Set attach_image to true to attach the image the user uploaded.
    """

    attachment = None
    if attach_image:
        image = get_image()
        if image is None:
            return (
                "No image is attached, so the draft was not created. "
                "Ask the user to attach the image first."
            )
        attachment = image.path

    save_draft(to=to, subject=subject, body=body, attachment=attachment)

    return (
        "Draft saved. It will be shown to the user, who must confirm it "
        "before it is sent. The email has NOT been sent."
    )


@tool
def list_unread_emails_tool(max_results: int = 5):
    """Retrieve and display unread emails from Gmail."""

    return list_unread_emails(max_results=max_results)
