import * as vscode from "vscode";
import { streamCode, getCurrentSession, createSession, resetSession, requestAutocomplete, setModelState } from "./apiClient";

const LANGUAGES = ["python", "javascript", "typescript", "c++", "c"];

let statusBarItem: vscode.StatusBarItem;

let previousChatState: boolean | undefined;
let previousAutoState: boolean | undefined;

function updateStatusBar() {
    const config = vscode.workspace.getConfiguration("localAI");
    const chatOn = config.get<boolean>("enableChat");
    const autoOn = config.get<boolean>("enableAutocomplete");

    if (chatOn && autoOn) {
        statusBarItem.text = "$(hubot) AI: All On";
        statusBarItem.tooltip = "Chat and Autocomplete are active";
    } else if (chatOn) {
        statusBarItem.text = "$(comment-discussion) AI: Chat Only";
    } else if (autoOn) {
        statusBarItem.text = "$(symbol-event) AI: Auto Only";
    } else {
        statusBarItem.text = "$(circle-slash) AI: Off";
        statusBarItem.tooltip = "All AI features are disabled";
    }
    statusBarItem.show();
}

function removePrefix(completion: string, before: string): string {
    // Get last 200 chars of what user typed
    const suffix = before.slice(-200);
    
    // If completion starts with any part of it, remove that part
    for (let i = 0; i < suffix.length; i++) {
        if (completion.startsWith(suffix.slice(i))) {
            return completion.slice(suffix.length - i);
        }
    }
    return completion;
}

async function syncModelStates() {
    // Call this whenever settings change.
    
    const config = vscode.workspace.getConfiguration("localAI");
    const chatOn = config.get<boolean>("enableChat", false);
    const autoOn = config.get<boolean>("enableAutocomplete", false);

    // Only call backend if states actually changed
    if (previousChatState !== chatOn) {
        console.log(`Syncing chat model: ${chatOn ? "ON" : "OFF"}`);
        await setModelState("chat", chatOn);
        previousChatState = chatOn;
    }

    if (previousAutoState !== autoOn) {
        console.log(`Syncing autocomplete model: ${autoOn ? "ON" : "OFF"}`);
        await setModelState("autocomplete", autoOn);
        previousAutoState = autoOn;
    }

    updateStatusBar();
}

// --- INLINE PROVIDER (With Toggle Check) ---
class AIInlineCompletionProvider implements vscode.InlineCompletionItemProvider {
    async provideInlineCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        context: vscode.InlineCompletionContext,
        token: vscode.CancellationToken
    ): Promise<vscode.InlineCompletionItem[] | vscode.InlineCompletionList> {

        // 1. CHECK SETTING
        const config = vscode.workspace.getConfiguration("localAI");
        if (!config.get<boolean>("enableAutocomplete")) {
            return [];
        }

        if (token.isCancellationRequested) return [];

        try {
            const beforeRange = new vscode.Range(new vscode.Position(0, 0), position);
            const before = document.getText(beforeRange);

            const afterRange = new vscode.Range(
                position,
                document.positionAt(document.offsetAt(position) + 1000)
            );
            const after = document.getText(afterRange);

            const completions = await requestAutocomplete(before, after, document.languageId, 64, 1);

            if (!completions || completions.length === 0) return [];
            if (token.isCancellationRequested) return [];

            const text = completions[0];
            let cleanText = text.replace(/^```\w*\n?/, "").replace(/\n?```$/, "");
            cleanText = removePrefix(cleanText, before);  

            return [
                new vscode.InlineCompletionItem(
                    cleanText,
                    new vscode.Range(position, position)
                )
            ];

        } catch (err) {
            console.error("Inline Autocomplete Error:", err);
            return [];
        }
    }
}

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
    const config = vscode.workspace.getConfiguration("localAI");
    if (!config.get<boolean>("enableChat")) {
        vscode.window.showWarningMessage(
            "Chat assistant is disabled. Enable it in the status bar to use this feature.",
            "Enable Now"
        ).then(selection => {
            if (selection === "Enable Now") {
                vscode.commands.executeCommand("simple-code-agent.toggleSettings");
            }
        });
        return;
    }
    
    const outputChannel = vscode.window.createOutputChannel("AI Assistant");
    outputChannel.show(true);
    outputChannel.appendLine(`🧠 Task: ${instruction}\n`);

    const sid = await ensureSession();

    try {
        await streamCode(code || "", instruction, (chunk: string) => {
            outputChannel.append(chunk); 
        }, sid);
    } catch (err: any) {
        if (err.message.includes("503") || err.message.includes("disabled")) {
            vscode.window.showErrorMessage(
                "Chat assistant is disabled on the backend. Please enable it.",
                "Enable Now"
            ).then(selection => {
                if (selection === "Enable Now") {
                    vscode.commands.executeCommand("simple-code-agent.toggleSettings");
                }
            });
        } else {
            vscode.window.showErrorMessage(`AI Assistant error: ${err.message}`);
        }
    }
}

export function activate(context: vscode.ExtensionContext) {
    console.log('Extension "simple-code-agent" is active!');

    // Initialize previous states
    const config = vscode.workspace.getConfiguration("localAI");
    previousChatState = config.get<boolean>("enableChat", false);
    previousAutoState = config.get<boolean>("enableAutocomplete", false);


    // 1. Commands 
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
            const sid = await getCurrentSession(); 
            await resetSession(sid);
            vscode.window.showInformationMessage(`✅ AI Assistant memory cleared for session ${sid}`);
        } catch {
            vscode.window.showInformationMessage("No current session to reset. Ask the assistant first to create one.");
        }
    });

    // 2. Toggle Command (Quick Pick UI) ---
    const toggleDisposable = vscode.commands.registerCommand("simple-code-agent.toggleSettings", async () => {
        const config = vscode.workspace.getConfiguration("localAI");
        const currentChat = config.get<boolean>("enableChat");
        const currentAuto = config.get<boolean>("enableAutocomplete");

        const items = [
            { 
                label: `${currentChat ? "$(check)" : "$(circle-slash)"} Enable Chat Assistant`, 
                description: currentChat ? "Currently Active (Ram Used)" : "Currently Off (Ram Saved)",
                picked: currentChat 
            },
            { 
                label: `${currentAuto ? "$(check)" : "$(circle-slash)"} Enable Autocomplete`, 
                description: currentAuto ? "Currently Active (~1GB RAM)" : "Currently Off (Ram Saved)",
                picked: currentAuto 
            }
        ];

        const selection = await vscode.window.showQuickPick(items, {
            placeHolder: "Toggle features to free up resources",
            canPickMany: true
        });

        if (selection === undefined) {     // User cancelled
            return;
        }

        const newChatState = selection.some(i => i.label.includes("Enable Chat Assistant"));
        const newAutoState = selection.some(i => i.label.includes("Enable Autocomplete"));

        // Show progress indicator
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Updating AI models...",
            cancellable: false
        }, async (progress) => {
            progress.report({ increment: 0, message: "Updating settings..." });

            // 1. Update Settings
            await config.update("enableChat", newChatState, vscode.ConfigurationTarget.Global);
            await config.update("enableAutocomplete", newAutoState, vscode.ConfigurationTarget.Global);
            
            progress.report({ increment: 50, message: "Syncing with backend..." });

            // 2. Call Backend to Unload/Load Models 
            await setModelState("chat", newChatState);
            await setModelState("autocomplete", newAutoState);

            // 3. Update tracked states
            previousChatState = newChatState;
            previousAutoState = newAutoState;
            
            progress.report({ increment: 100, message: "Done!" });

            // 4. Update UI
            updateStatusBar();

            // Show result
            const chatStatus = newChatState ? "ON ✓" : "OFF";
            const autoStatus = newAutoState ? "ON ✓" : "OFF";
            vscode.window.showInformationMessage(
                `AI Updated: Chat ${chatStatus}, Autocomplete ${autoStatus}`
            );
        });
    });

    // 3. Status Bar 
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = "simple-code-agent.toggleSettings";
    context.subscriptions.push(statusBarItem);

    syncModelStates(); 

    // Listen for configuration changes (e.g. if user edits settings.json directly)
    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration(async e => {
            if (e.affectsConfiguration("localAI")) {
                console.log("Configuration changed, syncing model states...");
                await syncModelStates();
            }
        })
    );

    // 4. Register providers
    const inlineProvider = vscode.languages.registerInlineCompletionItemProvider(
        LANGUAGES,
        new AIInlineCompletionProvider()
    );

    context.subscriptions.push(askAIDisposable, resetDisposable, toggleDisposable, inlineProvider); 
    console.log("✅ AI Assistant extension fully activated");
}

export function deactivate() {
    console.log("AI Assistant extension deactivated");
}
