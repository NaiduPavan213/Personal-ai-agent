from agents.supervisor import supervisor
from utils.email_confirmation import run_turn


def content_to_text(content):
    """Some models return a list of content blocks instead of a string."""
    if isinstance(content, list):
        return "\n".join(
            item["text"]
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        )
    return content


def ask_supervisor(messages):
    response = supervisor.invoke({"messages": messages})
    return content_to_text(response["messages"][-1].content)


print("🤖 Personal Assistant")
print("Type 'exit' to quit.\n")

# Store the conversation
messages = []

while True:
    user_input = input("You: ")

    if user_input.lower() == "exit":
        break

    messages.append({"role": "user", "content": user_input})

    # Handles email confirmation, otherwise asks the supervisor
    reply = run_turn(messages, ask_supervisor)

    messages.append({"role": "assistant", "content": reply})

    print("\nAssistant:", reply)
