"""
Confirm-before-send for emails.

The email agent can only *draft* an email (see tools/email_tools.py). The
draft is stored here, shown to the user word for word, and sent only when
the user's next message is an explicit confirmation such as "send".

The confirmation check is plain code, not the LLM, so the model can never
send an email on its own -- even if an incoming email tells it to.

Note: there is one pending draft per running process, which fits this
single-user, locally run assistant.
"""

from dataclasses import dataclass
from itertools import count

from integrations.gmail import send_email


@dataclass
class EmailDraft:
    id: int
    to: str
    subject: str
    body: str


CONFIRM_REPLIES = {
    "send", "send it", "yes", "y", "yes send", "yes send it",
    "confirm", "ok send", "go ahead",
}
CANCEL_REPLIES = {
    "cancel", "no", "n", "don't send", "dont send", "discard", "stop",
}

_ids = count(1)
_pending: EmailDraft | None = None


def save_draft(to: str, subject: str, body: str) -> EmailDraft:
    """Store a new draft, replacing any previous one."""
    global _pending
    _pending = EmailDraft(next(_ids), to, subject, body)
    return _pending


def get_pending() -> EmailDraft | None:
    return _pending


def clear_pending() -> None:
    global _pending
    _pending = None


def format_draft(draft: EmailDraft) -> str:
    return (
        "📝 **Please review this email before it is sent:**\n\n"
        f"**To:** {draft.to}\n"
        f"**Subject:** {draft.subject}\n\n"
        f"{draft.body}\n\n"
        "---\n"
        "Reply **send** to send it, or **cancel** to discard it. "
        "Any other reply discards this draft."
    )


def _normalize(text: str) -> str:
    return " ".join(
        text.strip().lower().replace(",", " ").rstrip(".!").split()
    )


def handle_pending_reply(message: str) -> str | None:
    """
    Handle the user's reply to a pending draft.

    Returns a reply to show the user if the message confirmed or cancelled
    the draft. Returns None if there was no draft, or if the message was
    something else (the draft is then discarded and the message should go
    to the assistant as usual).
    """
    draft = get_pending()
    if draft is None:
        return None

    reply = _normalize(message)
    clear_pending()

    if reply in CONFIRM_REPLIES:
        try:
            message_id = send_email(draft.to, draft.subject, draft.body)
        except Exception as error:
            return f"❌ The email could not be sent: {error}"
        return (
            f"✅ Email sent to {draft.to}.\n"
            f"Message ID: {message_id}"
        )

    if reply in CANCEL_REPLIES:
        return "🗑️ Draft discarded. The email was not sent."

    return None


def run_turn(messages: list, invoke) -> str:
    """
    Run one conversation turn with email confirmation.

    `messages` is the conversation including the new user message last;
    `invoke` calls the supervisor with those messages and returns its
    reply text.
    """
    user_message = messages[-1]["content"]

    direct_reply = handle_pending_reply(user_message)
    if direct_reply is not None:
        return direct_reply

    before = get_pending()
    reply = invoke(messages)
    after = get_pending()

    # A new draft was created this turn: show it exactly as it will be
    # sent, rather than the model's paraphrase of it.
    if after is not None and (before is None or after.id != before.id):
        return format_draft(after)

    return reply
