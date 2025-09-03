import { reporters } from "mocha";
import { syncBuiltinESMExports } from "module";
import { decode } from "punycode";

export async function streamCode(
    code: string, 
    instruction: string, 
    sessionID: string, 
    onChunk: (chunk: string) => void
) {
    const response = await fetch("http://localhost:8000/stream-code", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({code, instruction}),
    })

    const reader =  response.body?.getReader();
    const decoder = new TextDecoder("utf-8");

    while(true){
        const {done, value} = await reader!.read();
        if (done) break;
        const chunk = decoder.decode(value);
        onChunk(chunk);
    }
}

export async function resetSession(sessionId: string = "default") {
    const response = await fetch("http://localhost:8000/reset-session",{
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({"session_id": sessionId}),
        });
    
    if(!response.ok){
        throw new Error("Failed to reset session");
    }	
    
    return await response.json();
}