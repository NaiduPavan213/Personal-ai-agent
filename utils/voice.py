"""
Voice support: speech-to-text and text-to-speech.

- Speech-to-text uses Groq's hosted Whisper model (uses GROQ_API_KEY).
- Text-to-speech uses edge-tts (free Microsoft neural voices, no API key,
  needs an internet connection).
"""

import os
import re
import tempfile
import time
from pathlib import Path

import edge_tts
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

STT_MODEL = os.getenv("STT_MODEL", "whisper-large-v3-turbo")

# Any edge-tts voice name, e.g. "en-IN-NeerjaNeural", "en-GB-SoniaNeural".
# List them with:  edge-tts --list-voices
TTS_VOICE = os.getenv("TTS_VOICE", "en-US-AriaNeural")

# Long replies (e.g. several emails) are cut off so speech stays short.
MAX_SPOKEN_CHARS = 1200

AUDIO_DIR = Path(tempfile.gettempdir()) / "personal_assistant_audio"

_groq_client = None


def _client() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _groq_client


def transcribe(audio_path: str) -> str:
    """Convert a recorded audio file into text."""
    with open(audio_path, "rb") as audio_file:
        result = _client().audio.transcriptions.create(
            file=(Path(audio_path).name, audio_file.read()),
            model=STT_MODEL,
        )
    return result.text.strip()


def clean_for_speech(text: str) -> str:
    """Remove markdown, links and emoji so the reply sounds natural."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)      # [label](url)
    text = re.sub(r"https?://\S+", "a link", text)              # bare URLs
    text = re.sub(r"[*_`#>|]+", "", text)                        # markdown
    text = re.sub(r"^-{3,}\s*$", "", text, flags=re.MULTILINE)   # rules
    text = re.sub(
        "[\U0001F000-\U0001FAFF☀-➿️‍]", "", text
    )                                                             # emoji
    # Paragraph breaks become pauses (add a full stop only if none is there)
    text = re.sub(r"([^.!?:,;\s])[ \t]*\n{2,}", r"\1.\n", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"[ \t]+", " ", text).strip()

    if len(text) > MAX_SPOKEN_CHARS:
        text = text[:MAX_SPOKEN_CHARS].rsplit(" ", 1)[0]
        text += "... The rest is shown on screen."
    return text


def _delete_old_audio(max_age_seconds: int = 3600) -> None:
    """Remove spoken replies older than an hour so temp files don't pile up."""
    now = time.time()
    for file in AUDIO_DIR.glob("*.mp3"):
        try:
            if now - file.stat().st_mtime > max_age_seconds:
                file.unlink()
        except OSError:
            pass  # file in use or already gone


def speak(text: str) -> str | None:
    """Turn text into speech. Returns the path of an MP3 file, or None."""
    text = clean_for_speech(text)
    if not text:
        return None

    AUDIO_DIR.mkdir(exist_ok=True)
    _delete_old_audio()
    fd, path = tempfile.mkstemp(suffix=".mp3", dir=AUDIO_DIR)
    os.close(fd)

    edge_tts.Communicate(text, TTS_VOICE).save_sync(path)
    return path
