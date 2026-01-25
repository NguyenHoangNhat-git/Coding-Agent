from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import uuid, os
from autocomplete import router as autocomplete_router
import requests
from agent_processor import stream_model

from db import (
    get_messages,
    clear_messages,
    create_session,
    set_current_session,
    get_current_session,
    session_exists,
    list_sessions,
)

from models_manager import (
    set_chat_enabled,
    set_autocomplete_enabled,
    is_chat_enabled,
    is_autocomplete_enabled,
    initialize_models,
    CHAT_MODEL,
    AUTO_MODEL,
)

OLLAMA_API = os.getenv("OLLAMA_API", "http://localhost:11434/api/generate")

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    initialize_models(chat_enabled=False, auto_enabled=True)

class ModelStateRequest(BaseModel):
    feature: str  # "chat" or "autocomplete"
    enable: bool


@app.post("/manage-model")
def manage_model(req: ModelStateRequest):
    """
    Enable/disable models and tell Ollama to load/unload them.
    """
    model_name = CHAT_MODEL if req.feature == "chat" else AUTO_MODEL

    # Update internal state FIRST
    if req.feature == "chat":
        set_chat_enabled(req.enable)
    elif req.feature == "autocomplete":
        set_autocomplete_enabled(req.enable)
    else:
        return {"status": "error", "detail": f"Unknown feature: {req.feature}"}

    keep_alive = -1 if req.enable else 0

    payload = {"model": model_name, "keep_alive": keep_alive}

    try:
        if req.enable:
            payload["prompt"] = ""  # Force load into VRAM

        response = requests.post(OLLAMA_API, json=payload, timeout=10)

        action = "🔥 Loaded" if req.enable else "❄️ Unloaded"
        print(f"{action} {model_name} (keep_alive: {keep_alive})")

    except Exception as e:
        print(f"Failed to update model {model_name}: {e}")
        return {"status": "error", "detail": str(e)}

    return {
        "status": "success",
        "model": model_name,
        "feature": req.feature,
        "enabled": req.enable,
        "ollama_state": "loaded" if req.enable else "unloaded",
    }


class CodeRequest(BaseModel):
    code: str
    instruction: str
    session_id: Optional[str] = None


@app.post("/stream-code")
def stream_code(request: CodeRequest):

    if not is_chat_enabled():
        raise HTTPException(
            status_code=503,
            detail="Chat assistant is currently disabled. Enable it in VSCode settings.",
        )

    if not request.session_id:
        raise HTTPException(status_code=400, detail="session_id is required.")

    sid = request.session_id
    if not session_exists(sid):
        raise HTTPException(status_code=404, detail="session not found")

    memory = get_messages(sid, limit=50)

    generator = stream_model(
        code=request.code,
        instruction=request.instruction,
        memory=memory,
        session_id=sid,
    )

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# existing session endpoints


class CreateSessionRequest(BaseModel):
    session_id: Optional[str] = None
    name: Optional[str] = None
    make_current: bool = False


@app.post("/sessions")
def create_session_endpoint(req: CreateSessionRequest):
    sid = req.session_id or uuid.uuid4().hex
    create_session(session_id=sid, name=req.name, make_current=req.make_current)
    return {"session_id": sid}


@app.get("/sessions")
def list_sessions_endpoint():
    return {"sessions": list_sessions()}


@app.get("/current-session")
def get_current_session_endpoint():
    sid = get_current_session()
    if not sid:
        raise HTTPException(status_code=404, detail="no current session set")
    return {"session_id": sid}


class SetCurrentRequest(BaseModel):
    session_id: str


@app.post("/current-session")
def set_current_session_endpoint(req: SetCurrentRequest):
    if not session_exists(req.session_id):
        raise HTTPException(status_code=404, detail="session not found")
    set_current_session(req.session_id)
    return {"status": "ok", "session_id": req.session_id}


class ResetRequest(BaseModel):
    session_id: Optional[str] = None


@app.post("/reset-session")
def reset_session_endpoint(request: ResetRequest):
    sid = request.session_id or get_current_session()
    if not sid:
        raise HTTPException(status_code=404, detail="no session to reset")
    if not session_exists(sid):
        raise HTTPException(status_code=404, detail="session not found")
    cleared = clear_messages(sid)
    if not cleared:
        raise HTTPException(
            status_code=404, detail="session not found or nothing to clear"
        )
    return {"status": "cleared", "session_id": sid}


@app.get("/session/{session_id}")
def get_session_endpoint(session_id: str):
    return {"session_id": session_id, "messages": get_messages(session_id=session_id)}


app.include_router(autocomplete_router)
