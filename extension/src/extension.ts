import { EOF } from 'dns';
import * as vscode from 'vscode';
import { streamCode, resetSession } from './apiClient';

async function callAgent(instruction: string, code?: string) {
	const outputChannel = vscode.window.createOutputChannel("AI assistant");
	outputChannel.show(true);
	outputChannel.appendLine(`🧠 Task: ${instruction}\n`);

	await streamCode(code || "", instruction, (chunk: string) => {
		outputChannel.append(chunk);
	});
}

const sessionID = vscode.env.sessionId;

export function activate(context: vscode.ExtensionContext) {
	console.log('Congratulations, your extension "simple-code-agent" is now active!');

	// Command: highlight a code and ask agent about it
	const askAIDisposable = vscode.commands.registerCommand('simple-code-agent.askAgent', async () => {
		const editor = vscode.window.activeTextEditor;
		let code = "";

		if(editor){
			code = editor.document.getText(editor.selection);
		}

		const instruction = await vscode.window.showInputBox({
			prompt: code ? "What do you want to do with the code" : "Ask the AI assistant anything about coding",
			value: code ? "Explain this function" : "",
		})

		if(!instruction) return;

		await callAgent(instruction, code);
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


	context.subscriptions.push(askAIDisposable);
	context.subscriptions.push(resetDiposable);
}

// This method is called when your extension is deactivated
export function deactivate() {}
