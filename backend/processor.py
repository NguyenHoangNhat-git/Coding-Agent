from ollama import chat, Client
from typing import Generator, List, Dict
from .db import get_messages, append_messages

Message = Dict[str, str]

# Create one client per process so the model can stay warm
client = Client(host="http://127.0.0.1:11434")

SYSTEM_PROMPT = (
    "You are a helpful AI coding assistant. Be concise and use Markdown for code."
)


def stream_model(
    code: str, instruction: str, session_id: str
) -> Generator[str, None, None]:
    """
    Streams model output using Ollama's chat API and stores messages in MongoDB via db.py.
    """

    # Fetch previous messages from DB
    memory: List[Message] = get_messages(session_id=session_id)

    # Build chat history
    messages: List[Message] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(memory)
    messages.append(
        {
            "role": "user",
            "content": f"Task: {instruction}\n\nCode:\n```text\n{code}\n```",
        }
    )

    # Save user message to DB
    append_messages(
        session_id, "user", instruction if not code else f"{instruction}\n\n{code}"
    )

    # Stream from model. `keep_alive` helps keep the model loaded between calls.
    stream = client.chat(
        model="qwen2.5-coder:7b",
        messages=messages,
        stream=True,
        keep_alive="20m",
        # options={
        # "temperature": 0.2,
        # "num_ctx": 8192,
        # },
    )

    assistant_reply = ""

    for chunk in stream:
        msg = chunk.get("message", {})
        content = msg.get("content")
        if content:
            assistant_reply += content
            yield content

    # Save assistant reply
    if assistant_reply.strip():
        append_messages(session_id, "assistant", assistant_reply)
