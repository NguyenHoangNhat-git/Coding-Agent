import * as vscode from "vscode";
import { streamCode, getCurrentSession, createSession, resetSession, requestAutocomplete } from "./apiClient";

const LANGUAGES = ["python", "javascript", "typescript", "c++", "c"];

async function ensureSession(): Promise<string> {
    try {
        const sid = await getCurrentSession();
        return sid;
    } catch {
        const sid = await createSession("vscode-session", true);
        return sid;
    }
}

async function callAgent(instruction: string, code?: string) {
    const outputChannel = vscode.window.createOutputChannel("AI Assistant");
    outputChannel.show(true);
    outputChannel.appendLine(`🧠 Task: ${instruction}\n`);

    const sid = await ensureSession();

    try {
        await streamCode(code || "", instruction, (chunk: string) => {
            outputChannel.append(chunk); // stream tokens live
        }, sid);
    } catch (err: any) {
        vscode.window.showErrorMessage(`AI Assistant error: ${err.message}`);
    }
}

const provider = vscode.languages.registerCompletionItemProvider(
  LANGUAGES,
  {
    async provideCompletionItems(document: vscode.TextDocument, position: vscode.Position) {
      try {
        // Get up to N chars around cursor
        const beforeRange = new vscode.Range(new vscode.Position(0, 0), position);
        const before = document.getText(beforeRange);

        // a little after text (first 1000 chars)
        const afterRange = new vscode.Range(
            position,
            document.positionAt(
                Math.min(document.getText().length, document.offsetAt(position) + 3000)
            )
        );
        const after = document.getText(afterRange);
        // call backend
        const completions = await requestAutocomplete(before, after, document.languageId, 64, 3);
        if (!completions || completions.length === 0) return [];

        return completions.map((text) => {
          const item = new vscode.CompletionItem(text.split("\n")[0], vscode.CompletionItemKind.Snippet);
          item.insertText = new vscode.SnippetString(text);
          item.detail = "AI completion";
          item.documentation = new vscode.MarkdownString("AI-powered completion (local)");
          return item;
        });
      } catch (err: any) {
        console.error("Autocomplete error:", err);
        return [];
      }
    },
  },
  ".", "(", "," // trigger chars 
);

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
            const sid = await getCurrentSession(); // may throw 404
            await resetSession(sid);
            vscode.window.showInformationMessage(`✅ AI Assistant memory cleared for session ${sid}`);
        } catch {
            vscode.window.showInformationMessage("No current session to reset. Ask the assistant first to create one.");
        }
    });

    context.subscriptions.push(askAIDisposable, resetDisposable, provider); 
}

export function deactivate() {}
