// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import { EOF } from 'dns';
import * as vscode from 'vscode';
import { streamCode } from './apiClient';

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {

	// Use the console to output diagnostic information (console.log) and errors (console.error)
	// This line of code will only be executed once when your extension is activated
	console.log('Congratulations, your extension "simple-code-agent" is now active!');

	// The command has been defined in the package.json file
	// Now provide the implementation of the command with registerCommand
	// The commandId parameter must match the command field in package.json
	const disposable = vscode.commands.registerCommand('simple-code-agent.explainCode', async () => {
		// The code you place here will be executed every time your command is executed
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

		await streamCode(code, instruction, (chunk : string) => {
			outputChannel.appendLine(chunk);
		})
	});

	context.subscriptions.push(disposable);
}

// This method is called when your extension is deactivated
export function deactivate() {}
