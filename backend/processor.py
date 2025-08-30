import subprocess
import json


def stream_model(code: str, instruction: str) -> str:
    prompt = f"""
            You are a helpful AI coding assistant.

            Task: {instruction}

            Code:
            ```python
            {code}"""

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

    # Ensure clean shutdown
    process.stdout.close()
    process.wait()
