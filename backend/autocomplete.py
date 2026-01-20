# autocomplete.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Generator
from langchain_ollama import ChatOllama

# --- CONFIGURATION ---
# Use a small, fast model specifically for autocomplete.
# Run: `ollama pull qwen2.5-coder:1.5b` (or 0.5b for extreme speed)
AUTOCOMPLETE_MODEL = "qwen2.5-coder:1.5b"

# Independent client - NO tools bound, LOW temperature
llm_code = ChatOllama(model=AUTOCOMPLETE_MODEL, temperature=0.1)

router = APIRouter()


class AutocompleteRequest(BaseModel):
    before: str
    after: Optional[str] = ""
    language: Optional[str] = "plain"
    max_tokens: Optional[int] = 128
    top_k: Optional[int] = 1


@router.post("/autocomplete")
async def autocomplete(req: AutocompleteRequest):
    """
    Fast code completion endpoint.
    """
    prompt = build_prompt(req.before, req.after, req.language)

    try:
        # We don't use 'messages' here effectively because generic FIM
        # works best as a raw string or simple prompt for these models.
        # But ChatOllama requires messages.
        response = llm_code.invoke(
            [
                {
                    "role": "system",
                    "content": f"You are a fast {req.language} code completion engine. Output ONLY code. No markdown.",
                },
                {"role": "user", "content": prompt},
            ]
        )

        content = response.content

        # Clean up common chat-model artifacts (markdown blocks)
        cleaned = content.replace("```" + req.language, "").replace("```", "").strip()

        return {"completions": [cleaned]}

    except Exception as e:
        # Fail silently or gracefully for autocomplete
        print(f"Autocomplete Error: {e}")
        return {"completions": []}


def build_prompt(before: str, after: str, language: str) -> str:
    """
    Constructs a context-aware prompt.
    Note: Real FIM models (like DeepSeek/Qwen) support specific tokens
    <|fim_prefix|>, <|fim_suffix|>, <|fim_middle|>, but this generic structure
    works well across most instruction-tuned coders.
    """
    # Keep context short for speed
    safe_before = before[-1000:]
    safe_after = after[:500]

    return (
        f"### Context ({language}):\n"
        f"{safe_before}<CURSOR>{safe_after}\n\n"
        "### Instruction:\n"
        "Fill in the code at <CURSOR>. Provide only the missing code block."
    )


@router.post("/stream-autocomplete")
def stream_autocomplete(request: AutocompleteRequest):
    """
    Streaming autocomplete endpoint (text/plain). Yields the completion as it arrives.
    Useful for inline ghost text streaming.
    """
    prompt = build_prompt(request.before, request.after or "", request.language)
    try:
        stream = (
            llm_code.stream(  # depends on provider; some llm clients provide .stream
                model=getattr(llm_code, "model", None) or None,
                messages=[
                    {"role": "system", "content": "You are a code completion model."},
                    {"role": "user", "content": prompt},
                ],
                stream=True,
            )
        )
    except Exception:
        # Fallback: call non-streaming and yield result
        try:
            res = llm_code.invoke(
                [
                    {"role": "system", "content": "You are a code completion model."},
                    {"role": "user", "content": prompt},
                ]
            )
            text = getattr(res, "content", None) or str(res)

            def gen_once():
                yield text

            return gen_once()
        except Exception as e:

            def gen_err():
                yield f"[Error] {e}"

            return gen_err()

    def generator() -> Generator[str, None, None]:
        for chunk in stream:
            # chunk might be dicts / messages depending on provider; try to extract
            try:
                if isinstance(chunk, dict):
                    msg = chunk.get("message") or chunk.get("content") or chunk
                    if isinstance(msg, dict):
                        content = msg.get("content") or msg.get("text") or ""
                    else:
                        content = str(msg)
                else:
                    content = str(chunk)
            except Exception:
                content = str(chunk)
            yield content

    return generator()
