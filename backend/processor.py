import subprocess
import json


def stream_model(code: str, instruction: str, memory: list):
    # build prompt from memory
    conversation = ""
    for msg in memory:
        role = msg["role"].upper()
        content = msg["content"]
        conversation += f"{role}: {content}\n\n"

    # add lastest user request
    conversation += f"USER: Code:\n{code}\nInstruction:\n{instruction}\n\n"

    prompt = f"""
            You are a helpful AI coding assistant.

            Previous conversations: {conversation}

            Task: {instruction}

            Code:
            ```python
            {code}
            ```"""

    process = subprocess.Popen(
        ["ollama", "run", "qwen2.5-coder:7b"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        text=True,  # Enable text streaming (not binary)
    )

    # Feed prompt
    process.stdin.write(prompt)
    process.stdin.close()

    # Yield output line by line
    for line in process.stdout:
        # yield f'{{"chunk": {json.dumps(line)}}}\n'
        yield line.rstrip("\n")

    process.stdout.close()
    process.wait()
