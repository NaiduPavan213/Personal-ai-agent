import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

response = client.chat.completions.with_raw_response.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Hello"}]
)

print("\nGROQ RATE LIMIT HEADERS:")

for name, value in response.headers.items():
    if "ratelimit" in name.lower():
        print(f"{name}: {value}")