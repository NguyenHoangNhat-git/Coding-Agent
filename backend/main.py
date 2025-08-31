from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from processor import stream_model

app = FastAPI()

sessions = {}
# {session_id: [{"role": "user", "content": ...}, {"role": "assistant", "content": ...}]}


class CodeRequest(BaseModel):
    code: str
    instruction: str
    session_id: str = "default"


@app.post("/stream-code")
def stream_code(request: CodeRequest):
    session_id = request.session_id
    # init session memory
    memory = sessions.setdefault(session_id, [])

    # append user's message
    user_message = f"Instruction: {request.instruction}\nCode:\n{request.code}"
    memory.append({"role": "user", "content": user_message})

    generator = stream_model(
        code=request.code, instruction=request.instruction, memory=memory
    )

    def stream_and_store():
        assistant_reply = ""
        for chunk in generator:
            assistant_reply += chunk
            yield chunk

        memory.append({"role": "assistant", "content": assistant_reply})

    return StreamingResponse(stream_and_store(), media_type="text/plain")
