"""
The image the user attached in the current conversation.

The latest attached image stays "current" until another image is attached
or a new chat is started, so follow-ups like "email it to Ravi" work.

Note: there is one current image per running process, which fits this
single-user, locally run assistant (same as the pending email draft).
"""

import base64
import mimetypes
from dataclasses import dataclass
from pathlib import Path

# Gmail allows 25 MB per email; keep well under it
MAX_IMAGE_BYTES = 10 * 1024 * 1024


@dataclass
class Attachment:
    path: str
    name: str
    mime_type: str


_current: Attachment | None = None


def check_image(path: str) -> str:
    """Return the image's MIME type. Raises ValueError if it can't be used."""
    file = Path(path)
    mime_type = mimetypes.guess_type(file.name)[0] or ""

    if not mime_type.startswith("image/"):
        raise ValueError("Only image files can be attached.")
    if file.stat().st_size > MAX_IMAGE_BYTES:
        raise ValueError("Images must be smaller than 10 MB.")
    return mime_type


def set_image(path: str) -> Attachment:
    """Make `path` the current image. Raises ValueError if it can't be used."""
    global _current
    mime_type = check_image(path)
    _current = Attachment(str(path), Path(path).name, mime_type)
    return _current


def get_image() -> Attachment | None:
    return _current


def clear_image() -> None:
    global _current
    _current = None


def image_data_url(image: Attachment) -> str:
    """The image as a base64 data URL, as vision models expect."""
    data = base64.b64encode(Path(image.path).read_bytes()).decode()
    return f"data:{image.mime_type};base64,{data}"
