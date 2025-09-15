import * as vscode from "vscode";
import { streamCode, getCurrentSession, createSession, resetSession } from "./apiClient";

async function ensureSession(): Promise<string> {
    try {
        // Try to get the current session (will throw if none)
        const sid = await getCurrentSession();
        return sid;
    } catch (err) {
        // If no current session, create one and mark it current
        const sid = await createSession("vscode-session", true);
        return sid;
    }
}

async function callAgent(instruction: string, code?: string) {
    const outputChannel = vscode.window.createOutputChannel("AI Assistant");
    outputChannel.show(true);
    outputChannel.appendLine(`🧠 Task: ${instruction}\n`);

    const sid = await ensureSession();

    await streamCode(code || "", instruction, (chunk: string) => {
        outputChannel.append(chunk);
    }, sid);
}

export function activate(context: vscode.ExtensionContext) {
    console.log('Extension "simple-code-agent" is active!');

    const askAIDisposable = vscode.commands.registerCommand("simple-code-agent.askAgent", async () => {
        const editor = vscode.window.activeTextEditor;
        let code = "";
        if (editor) code = editor.document.getText(editor.selection);

        const instruction = await vscode.window.showInputBox({
            prompt: code ? "What do you want to do with the code?" : "Ask the AI assistant anything about coding",
            value: code ? "Explain this function" : "",
        });
        if (!instruction) return;

        await callAgent(instruction, code);
    });

    const resetDisposable = vscode.commands.registerCommand("simple-code-agent.resetSession", async () => {
        try {
            // Check whether a current session exists (GET /current-session)
            const sid = await getCurrentSession(); // will throw if none
            // If we have one, clear it. This call will NOT create a new session.
            await resetSession(sid);
            vscode.window.showInformationMessage(`✅ AI Assistant memory cleared for session ${sid}`);
        } catch (err: any) {
            // If getCurrentSession threw 404 -> show friendly message
            vscode.window.showInformationMessage("No current session to reset. Create a new session by asking the assistant.");
        }
    });

    context.subscriptions.push(askAIDisposable);
    context.subscriptions.push(resetDisposable);
}

export function deactivate() {}
