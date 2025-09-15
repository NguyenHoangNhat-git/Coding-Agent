import * as vscode from "vscode";
import { streamCode, resetSession, createSession } from "./apiClient";

let sessionID: string | null = null;


async function ensureSession() {
    if (!sessionID) {
        sessionID = await createSession("vscode-session", true);
    }
    return sessionID;
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

    // Command: highlight code and ask AI
    const askAIDisposable = vscode.commands.registerCommand("simple-code-agent.askAgent", async () => {
        const editor = vscode.window.activeTextEditor;
        let code = "";

        if (editor) {
            code = editor.document.getText(editor.selection);
        }

        const instruction = await vscode.window.showInputBox({
            prompt: code ? "What do you want to do with the code?" : "Ask the AI assistant anything about coding",
            value: code ? "Explain this function" : "",
        });

        if (!instruction) return;

        await callAgent(instruction, code);
    });

    // Command: reset current session
    const resetDisposable = vscode.commands.registerCommand("simple-code-agent.resetSession", async () => {
        try {
            const sid = await ensureSession();
            await resetSession(sid);
            vscode.window.showInformationMessage("✅ AI Assistant memory has been reset!");
        } catch (err: any) {
            vscode.window.showErrorMessage("❌ Failed to reset memory: " + err.message);
        }
    });

    context.subscriptions.push(askAIDisposable, resetDisposable);
}

export function deactivate() {}
