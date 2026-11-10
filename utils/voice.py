"""
Voice input: speech-to-text using Groq's hosted Whisper model
(uses GROQ_API_KEY).
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

STT_MODEL = os.getenv("STT_MODEL", "whisper-large-v3-turbo")

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
