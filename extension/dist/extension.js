"use strict";
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/extension.ts
var extension_exports = {};
__export(extension_exports, {
  activate: () => activate,
  deactivate: () => deactivate
});
module.exports = __toCommonJS(extension_exports);
var vscode = __toESM(require("vscode"));

// src/apiClient.ts
async function streamCode(code, instruction, sessionID2, onChunk) {
  const response = await fetch("http://localhost:8000/stream-code", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ code, instruction })
  });
  const reader = response.body?.getReader();
  const decoder = new TextDecoder("utf-8");
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value);
    onChunk(chunk);
  }
}
async function resetSession(sessionId = "default") {
  const response = await fetch("http://localhost:8000/reset-session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ "session_id": sessionId })
  });
  if (!response.ok) {
    throw new Error("Failed to reset session");
  }
  return await response.json();
}

// src/extension.ts
var sessionID = vscode.env.sessionId;
function activate(context) {
  console.log('Congratulations, your extension "simple-code-agent" is now active!');
  const disposable = vscode.commands.registerCommand("simple-code-agent.explainCode", async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showErrorMessage("No code selected");
      return;
    }
    const code = editor.document.getText(editor.selection);
    if (!code) {
      vscode.window.showInformationMessage("Please select some code first");
      return;
    }
    const instruction = await vscode.window.showInputBox({
      prompt: "What do you want to do with the code",
      value: "Explain this function"
    });
    if (!instruction) return;
    const outputChannel = vscode.window.createOutputChannel("AI assistant(Qwen 2.5 7B)");
    outputChannel.show(true);
    outputChannel.appendLine(`\u{1F9E0} Task: ${instruction}
`);
    await streamCode(code, instruction, sessionID, (chunk) => {
      outputChannel.appendLine(chunk);
    });
  });
  const resetDiposable = vscode.commands.registerCommand("simple-code-agent.resetSession", async () => {
    try {
      await resetSession(sessionID);
      vscode.window.showInformationMessage("\u2705 AI Assistant memory has been reset!");
    } catch (err) {
      vscode.window.showErrorMessage("\u274C Failed to reset memory: " + err);
    }
  });
  context.subscriptions.push(disposable);
  context.subscriptions.push(resetDiposable);
}
function deactivate() {
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  activate,
  deactivate
});
//# sourceMappingURL=extension.js.map
