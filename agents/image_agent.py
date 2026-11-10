from langchain_core.messages import HumanMessage, SystemMessage

from prompts.image_prompt import IMAGE_PROMPT
from utils.attachments import get_image, image_data_url
from utils.llm import vision_llm


def content_to_text(content) -> str:
    """Gemini can return a list of content blocks instead of a string."""
    if isinstance(content, list):
        return "\n".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        ).strip()
    return content


def answer_about_image(question: str) -> str:
    """Answer a question about the currently attached image."""
    image = get_image()
    if image is None:
        return (
            "No image is attached. Use the 📎 button in the message box "
            "to attach one, then ask your question."
        )

    try:
        response = vision_llm.invoke([
            SystemMessage(content=IMAGE_PROMPT),
            HumanMessage(content=[
                {"type": "text", "text": question},
                {"type": "image_url", "image_url": {"url": image_data_url(image)}},
            ]),
        ])
    except Exception as error:
        print(f"Vision model failed: {error}")
        return (
            "Sorry, the image model is busy right now. "
            "Please try your question again in a moment."
        )

    return content_to_text(response.content)
