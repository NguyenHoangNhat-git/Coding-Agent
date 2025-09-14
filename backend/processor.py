from ollama import chat, Client
from typing import Generator, List, Dict
from db import get_messages, append_messages

Message = Dict[str, str]

# Create one client per process so the model can stay warm
client = Client(host="http://127.0.0.1:11434")

SYSTEM_PROMPT = "You are a helpful AI coding assistant. Be concise (don't show detail unless being asked) and use Markdown for code."


def stream_model(
    code: str, instruction: str, memory: List[Message], session_id: str
) -> Generator[str, None, None]:
    """
    Streams model output using Ollama's chat API and saves conversation to MongoDB.
    `memory` is a list of {"role","content"} dicts.
    """
    # Load history from DB
    # memory = get_messages(session_id, limit=50)

    # Build chat history
    messages: List[Message] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(memory)
    messages.append(
        {
            "role": "user",
            "content": f"Task: {instruction}\n\nCode:\n```text\n{code}\n```",
        }
    )
    print(messages)

    # Save user message to DB
    append_messages(
        session_id, "user", f"Task: {instruction}\n\nCode:\n```text\n{code}\n```"
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
