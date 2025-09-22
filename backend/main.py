# main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import uuid

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

app = FastAPI()


class CodeRequest(BaseModel):
    code: str
    instruction: str
    session_id: Optional[str] = None


@app.post("/stream-code")
def stream_code(request: CodeRequest):
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
