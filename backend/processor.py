import subprocess
from ollama import chat, Client
from typing import Generator, List, Dict

Message = Dict[str, str]

# Create one client per process so the model can stay warm
client = Client(host="http://127.0.0.1:11434")

SYSTEM_PROMPT = (
    "You are a helpful AI coding assistant. Be concise and use Markdown for code."
)


def stream_model(
    code: str, instruction: str, memory: List[Message]
) -> Generator[str, None, None]:
    """
    Streams model output using Ollama's chat API. `memory` is a list of {"role","content"} dicts.
    """

    # Build the chat history for this request
    messages: List[Message] = [{"role": "system", "content": SYSTEM_PROMPT}]
    # Append prior conversations (main.py keeps this up-to-date)
    messages.extend(memory)
    messages.append(
        {
            "role": "user",
            "content": f"Task: {instruction}\n\nCode:\n```text\n{code}\n```",
        }
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

    for chunk in stream:
        msg = chunk.get("message", {})
        content = msg.get("content")
        if content:
            yield content
