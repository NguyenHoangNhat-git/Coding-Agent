import { EOF } from 'dns';
import * as vscode from 'vscode';
import { streamCode, resetSession } from './apiClient';

const sessionID = vscode.env.sessionId;

export function activate(context: vscode.ExtensionContext) {
	console.log('Congratulations, your extension "simple-code-agent" is now active!');

	// Command: highlight a code and ask agent about it
	const disposable = vscode.commands.registerCommand('simple-code-agent.explainCode', async () => {
		// Runs everytime a command is executed
		const editor = vscode.window.activeTextEditor;
		if(!editor){
			vscode.window.showErrorMessage("No code selected");
			return
		}

		const code = editor.document.getText(editor.selection);
		if(!code) {
			vscode.window.showInformationMessage("Please select some code first");
			return;
		}

		const instruction = await vscode.window.showInputBox({
			prompt: "What do you want to do with the code",
			value: "Explain this function",
		})

		if(!instruction) return;

		const outputChannel = vscode.window.createOutputChannel("AI assistant(Qwen 2.5 7B)");
		outputChannel.show(true);
		outputChannel.appendLine(`🧠 Task: ${instruction}\n`);

		await streamCode(code, instruction, sessionID, (chunk : string) => {
			outputChannel.append(chunk);
		})
	});


	// Command: Clear all conversations of the current session
	const resetDiposable = vscode.commands.registerCommand("simple-code-agent.resetSession", async () => {
		try{
			await resetSession(sessionID);
			vscode.window.showInformationMessage("✅ AI Assistant memory has been reset!");
		} catch(err){
			vscode.window.showErrorMessage("❌ Failed to reset memory: " + err);
		}
	})


	context.subscriptions.push(disposable);
	context.subscriptions.push(resetDiposable);
}

// This method is called when your extension is deactivated
export function deactivate() {}
