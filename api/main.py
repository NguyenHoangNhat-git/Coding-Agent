from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from processor import stream_model

app = FastAPI()

class CodeRequest(BaseModel):
    code: str
    instruction: str

@app.post("/process-code")
def stream_code(request: CodeRequest):
    generator = stream_model(code=request.code, instruction=request.instruction)
    return StreamingResponse(generator, media_type="text/plain")

    