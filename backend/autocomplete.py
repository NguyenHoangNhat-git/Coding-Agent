from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Generator
import json
import time

# Import the shared llm from agent_processor.py to reuse the warm model
try:
    from agent_processor import llm
except Exception:
    # Fallback: create a quick client if agent_processor not importable.
    from langchain_ollama import ChatOllama

    llm = ChatOllama(model="qwen2.5-coder:7b", temperature=0)

router = APIRouter()


class AutocompleteRequest(BaseModel):
    before: str
    after: Optional[str] = ""
    language: Optional[str] = "plain"
    max_tokens: Optional[int] = 64
    temperature: Optional[float] = 0.05
    top_k: Optional[int] = 1  # number of suggestions to return


@router.post("/autocomplete")
async def autocomplete(req: AutocompleteRequest):
    """
    Returns a small list of completion suggestions (non-streaming).
    """
    prompt = build_prompt(req.before, req.after, req.language)
    try:
        # Use conservative decoding params for deterministic completions
        # Using llm.invoke to return a message object (depends on provider)
        result = llm.invoke(
            [
                {
                    "role": "system",
                    "content": "You are a code completion model. Produce concise code continuations only.",
                },
                {"role": "user", "content": prompt},
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # result may be an AIMessage or similar; extract text robustly
    try:
        text = getattr(result, "content", None) or str(result)
    except Exception:
        text = str(result)

    completions = postprocess_completions(text, req.top_k)
    return {"completions": completions}


def build_prompt(before: str, after: str, language: str) -> str:
    """
    Enhanced prompt for structural code completion.
    Produces function bodies, class methods, etc.
    """
    # Use larger window for function-level completions
    snippet_before = before[-8000:]
    snippet_after = (after or "")[:2000]

    prompt = (
        f"### Code language: {language}\n"
        "You are a code completion model.\n"
        "Continue the code at the cursor <CURSOR>.\n\n"
        "Rules:\n"
        "- ONLY output the code to be inserted.\n"
        "- No explanations.\n"
        "- No backticks.\n"
        "- Continue logically using full indentation.\n"
        "- If inside a function or class, generate the entire block.\n"
        "- If the user typed a function signature, generate the full function body.\n"
        '- If multiple suggestions are required, separate them with "\n\n".\n\n'
        "### BEFORE\n"
        f"{snippet_before}"
        "\n<CURSOR>\n"
        "### AFTER\n"
        f"{snippet_after}\n\n"
        "### COMPLETION:\n"
    )

    return prompt


def postprocess_completions(text: str, top_k: int):
    """
    Given model text, split into up to top_k suggestions and trim whitespace.
    The model should ideally return single completion; we split by double-newline if multiple.
    """
    if not text:
        return []

    # Normalize and split
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not parts:
        parts = [text.strip()]

    # Limit to top_k
    parts = parts[: max(1, top_k)]
    return parts


@router.post("/stream-autocomplete")
def stream_autocomplete(request: AutocompleteRequest):
    """
    Streaming autocomplete endpoint (text/plain). Yields the completion as it arrives.
    Useful for inline ghost text streaming.
    """
    prompt = build_prompt(request.before, request.after or "", request.language)
    try:
        stream = llm.stream(  # depends on provider; some llm clients provide .stream
            model=getattr(llm, "model", None) or None,
            messages=[
                {"role": "system", "content": "You are a code completion model."},
                {"role": "user", "content": prompt},
            ],
            stream=True,
        )
    except Exception:
        # Fallback: call non-streaming and yield result
        try:
            res = llm.invoke(
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
