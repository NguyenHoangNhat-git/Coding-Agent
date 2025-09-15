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
var BASE = "http://127.0.0.1:8000";
async function streamCode(code, instruction, onChunk, session_id = "default") {
  const response = await fetch(`${BASE}/stream-code`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, instruction, session_id })
  });
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
async function resetSession(session_id = "default") {
  const response = await fetch(`${BASE}/reset-session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id })
  });
  if (!response.ok) {
    throw new Error("Failed to reset session");
  }
  return await response.json();
}
async function createSession(name, makeCurrent = false) {
  const res = await fetch(`${BASE}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, make_current: makeCurrent })
  });
  if (!res.ok) throw new Error("Failed to create session");
  const data = await res.json();
  return data.session_id;
}

// src/extension.ts
var sessionID = null;
async function ensureSession() {
  if (!sessionID) {
    sessionID = await createSession("vscode-session", true);
  }
  return sessionID;
}
async function callAgent(instruction, code) {
  const outputChannel = vscode.window.createOutputChannel("AI Assistant");
  outputChannel.show(true);
  outputChannel.appendLine(`\u{1F9E0} Task: ${instruction}
`);
  const sid = await ensureSession();
  await streamCode(code || "", instruction, (chunk) => {
    outputChannel.append(chunk);
  }, sid);
}
function activate(context) {
  console.log('Extension "simple-code-agent" is active!');
  const askAIDisposable = vscode.commands.registerCommand("simple-code-agent.askAgent", async () => {
    const editor = vscode.window.activeTextEditor;
    let code = "";
    if (editor) {
      code = editor.document.getText(editor.selection);
    }
    const instruction = await vscode.window.showInputBox({
      prompt: code ? "What do you want to do with the code?" : "Ask the AI assistant anything about coding",
      value: code ? "Explain this function" : ""
    });
    if (!instruction) return;
    await callAgent(instruction, code);
  });
  const resetDisposable = vscode.commands.registerCommand("simple-code-agent.resetSession", async () => {
    try {
      const sid = await ensureSession();
      await resetSession(sid);
      vscode.window.showInformationMessage("\u2705 AI Assistant memory has been reset!");
    } catch (err) {
      vscode.window.showErrorMessage("\u274C Failed to reset memory: " + err.message);
    }
  });
  context.subscriptions.push(askAIDisposable, resetDisposable);
}
function deactivate() {
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  activate,
  deactivate
});
//# sourceMappingURL=extension.js.map
