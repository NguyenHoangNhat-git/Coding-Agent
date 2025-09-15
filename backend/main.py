from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from processor import stream_model
from typing import Optional
import uuid

from db import (
    get_messages,
    append_messages,
    clear_messages,
    list_sessions,
    set_current_session,
    get_current_session,
)

app = FastAPI()


class CodeRequest(BaseModel):
    code: str
    instruction: str
    session_id: Optional[str] = None  # If not given, fallback to current session


@app.post("/stream-code")
def stream_code(request: CodeRequest):
    # Use provided session_id or fallback to current one
    sid = request.session_id or get_current_session() or "default"

    memory = get_messages(sid, limit=50)

    generator = stream_model(
        code=request.code,
        instruction=request.instruction,
        memory=memory,
        session_id=sid,
    )
    return StreamingResponse(generator, media_type="text/plain")


class CreateSessionRequest(BaseModel):
    session_id: Optional[str] = None
    name: Optional[str] = None
    make_current: bool = False


@app.post("/sessions")
def create_session_endpoint(req: CreateSessionRequest):
    # Use provided ID or generate one
    sid = req.session_id or str(uuid.uuid4())
    clear_messages(sid)  # ensure new doc is created
    if req.make_current:
        set_current_session(sid)
    return {"session_id": sid}


class ResetRequest(BaseModel):
    session_id: Optional[str] = None  # optional now


@app.post("/reset-session")
def reset_session_endpoint(request: ResetRequest):
    sid = request.session_id or get_current_session() or "default"
    clear_messages(sid)
    return {"status": "reset", "session_id": sid}


@app.get("/sessions")
def list_sessions_endpoint():
    return {"sessions": list_sessions()}


@app.get("/session/{session_id}")
def get_session(session_id: str):
    return {"session_id": session_id, "messages": get_messages(session_id=session_id)}


@app.get("/current-session")
def get_current_session_endpoint():
    sid = get_current_session() or "default"
    return {"session_id": sid}


class SetCurrentRequest(BaseModel):
    session_id: str


@app.post("/current-session")
def set_current_session_endpoint(req: SetCurrentRequest):
    set_current_session(req.session_id)
    return {"status": "ok", "session_id": req.session_id}
