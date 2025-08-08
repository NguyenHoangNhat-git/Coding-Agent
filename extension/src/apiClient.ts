import { decode } from "punycode";

export async function streamCode(code: string, instruction: string, onChunk: (chunk: string) => void) {
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