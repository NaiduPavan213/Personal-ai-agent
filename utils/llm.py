
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

load_dotenv()

# Primary provider: Groq
groq_llm = ChatGroq(
    model="openai/gpt-oss-120b",
    groq_api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
    max_tokens=1000,
)

# Second backup: Google Gemini
primary_llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0,
    max_output_tokens=1000,
    max_retries=1,
)

# First backup: OpenRouter free models
backup_llm = ChatOpenAI(
    model="openrouter/free",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0,
    max_tokens=1000,
)

# Try Groq first, then OpenRouter, then Gemini if a provider fails
llm = groq_llm.with_fallbacks([backup_llm, primary_llm])

print("LLM providers configured: Groq -> OpenRouter -> Gemini")


# Vision (questions about attached images): Groq has no vision models on
# this account, so images go to Gemini. If the main model is slow or
# overloaded, give up quickly and use the fast "lite" model instead.
def _gemini(model, timeout):
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=os.getenv("GEMINI_API_KEY"),
        max_output_tokens=1500,
        max_retries=0,
        timeout=timeout,
    )


vision_llm = _gemini(
    os.getenv("VISION_MODEL", "gemini-3.5-flash"), timeout=10
).with_fallbacks([
    _gemini("gemini-3.5-flash-lite", timeout=30),
])
