
import base64
import mimetypes
from email.message import EmailMessage
from pathlib import Path

from googleapiclient.discovery import build

from integrations.auth import authenticate_google


def get_gmail_service():
    """Create an authenticated Gmail API service."""
    creds = authenticate_google()
    return build("gmail", "v1", credentials=creds)


def send_email(to, subject, body, attachment_path=None):
    """Send an email using Gmail API, optionally with one attached file."""

    service = get_gmail_service()

    message = EmailMessage()
    message["to"] = to
    message["subject"] = subject
    message.set_content(body)

    if attachment_path:
        file = Path(attachment_path)
        mime_type = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
        maintype, subtype = mime_type.split("/", 1)
        message.add_attachment(
            file.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename=file.name,
        )

    raw_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    result = (
        service.users()
        .messages()
        .send(
            userId="me",
            body={"raw": raw_message},
        )
        .execute()
    )

    return result["id"]


def extract_email_body(payload):
    """Extract plain-text content from an email."""

    mime_type = payload.get("mimeType", "")

    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data")

        if data:
            return base64.urlsafe_b64decode(
                data
            ).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        body = extract_email_body(part)

        if body:
            return body

    return ""


def list_unread_emails(max_results=5):
    """Retrieve unread emails from Gmail."""

    service = get_gmail_service()

    results = (
        service.users()
        .messages()
        .list(
            userId="me",
            q="is:unread",
            maxResults=max_results,
        )
        .execute()
    )

    messages = results.get("messages", [])

    if not messages:
        return "You have no unread emails."

    output = []

    for message in messages:
        email = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=message["id"],
                format="full",
            )
            .execute()
        )

        headers = email.get("payload", {}).get("headers", [])

        sender = next(
            (h["value"] for h in headers if h["name"].lower() == "from"),
            "Unknown sender",
        )

        subject = next(
            (h["value"] for h in headers if h["name"].lower() == "subject"),
            "No subject",
        )

        body = extract_email_body(email.get("payload", {}))

        if not body:
            body = email.get("snippet", "No email content available.")

        output.append(
            f"From: {sender}\n"
            f"Subject: {subject}\n"
            f"Content: {body[:2000]}"
        )

    return "\n\n--------------------\n\n".join(output)
