from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from processor import stream_model

from db import get_messages, append_messages, reset_session

app = FastAPI()

sessions = {}
# {session_id: [{"role": "user", "content": ...}, {"role": "assistant", "content": ...}]}


class CodeRequest(BaseModel):
    code: str
    instruction: str
    session_id: str = "default"


@app.post("/stream-code")
def stream_code(request: CodeRequest):
    # Load the last N messages
    memory = get_messages(request.session_id, limit=50)

    generator = stream_model(
        code=request.code,
        instruction=request.instruction,
        memory=memory,
        session_id=request.session_id,
    )
    return StreamingResponse(generator, media_type="text/plain")


class ResetRequest(BaseModel):
    session_id: str = "default"


@app.post("/reset-session")
def reset_session_endpoint(request: ResetRequest):
    reset_session(request.session_id)
    return {"status": "reset", "session_id": request.session_id}


@app.get("/session/{session_id}")
def get_session(session_id: str):
    # return full messages (beware long histories)
    return {"session_id": session_id, "messages": get_messages(session_id=session_id)}
