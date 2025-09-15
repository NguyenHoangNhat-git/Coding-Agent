const BASE = "http://127.0.0.1:8000";

interface SessionResponse {
    session_id: string;
}

interface ResetResponse {
    status: string;
    session_id: string;
}

export async function streamCode(
    code: string,
    instruction: string,
    onChunk: (chunk: string) => void,
    session_id: string
) {
    const response = await fetch(`${BASE}/stream-code`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, instruction, session_id }),
    });

    if (!response.ok) {
        const txt = await response.text();
        throw new Error(`streamCode error: ${response.status} ${txt}`);
    }

    if (!response.body) throw new Error("No response body from server");

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        onChunk(chunk);
    }
}

export async function getCurrentSession(): Promise<string> {
    const res = await fetch(`${BASE}/current-session`);
    if (!res.ok) {
        // allow caller to handle 404 (no current session)
        const txt = await res.text();
        throw new Error(`getCurrentSession failed: ${res.status} ${txt}`);
    }
    const data = (await res.json()) as SessionResponse;
    return data.session_id;
}

export async function createSession(name?: string, makeCurrent: boolean = false): Promise<string> {
    const res = await fetch(`${BASE}/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, make_current: makeCurrent }),
    });
    if (!res.ok) {
        const txt = await res.text();
        throw new Error(`createSession failed: ${res.status} ${txt}`);
    }
    const data = (await res.json()) as SessionResponse;
    return data.session_id;
}

export async function resetSession(session_id: string): Promise<ResetResponse> {
    const res = await fetch(`${BASE}/reset-session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id }),
    });
    if (!res.ok) {
        const txt = await res.text();
        throw new Error(`resetSession failed: ${res.status} ${txt}`);
    }
    return (await res.json()) as ResetResponse;
}
