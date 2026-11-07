
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

load_dotenv()

groq_llm = ChatGroq(
    model="openai/gpt-oss-120b",
    groq_api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
    max_tokens=1000,
)

# Primary provider: Google Gemini
primary_llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0,
    max_output_tokens=1000,
    max_retries=1,
)

# Backup provider: OpenRouter free models
backup_llm = ChatOpenAI(
    model="openrouter/free",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0,
    max_tokens=1000,
)

# Automatically switch to backup if primary fails
llm = groq_llm.with_fallbacks([backup_llm, primary_llm])

print("LLM providers configured: Gemini -> OpenRouter")
