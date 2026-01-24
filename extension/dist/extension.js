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
async function streamCode(code, instruction, onChunk, session_id) {
  const response = await fetch(`${BASE}/stream-code`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, instruction, session_id })
  });
  if (!response.ok) {
    const txt = await response.text();
    if (response.status === 503) {
      throw new Error("Chat assistant is currently disabled. Please enable it in settings.");
    }
    throw new Error(`streamCode error: ${response.status} ${txt}`);
  }
  if (!response.body) throw new Error("No response body from server");
  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      onChunk(chunk);
    }
  } catch (error) {
    reader.cancel();
    throw error;
  }
}
async function getCurrentSession() {
  const res = await fetch(`${BASE}/current-session`);
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`getCurrentSession failed: ${res.status} ${txt}`);
  }
  const data = await res.json();
  return data.session_id;
}
async function createSession(name, makeCurrent = false) {
  const res = await fetch(`${BASE}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, make_current: makeCurrent })
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`createSession failed: ${res.status} ${txt}`);
  }
  const data = await res.json();
  return data.session_id;
}
async function resetSession(session_id) {
  const res = await fetch(`${BASE}/reset-session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id })
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`resetSession failed: ${res.status} ${txt}`);
  }
  return await res.json();
}
async function requestAutocomplete(before, after, language = "python", max_tokens = 64, top_k = 1) {
  const res = await fetch(`${BASE}/autocomplete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      before,
      after,
      language,
      max_tokens,
      top_k
    })
  });
  if (!res.ok) {
    console.warn(`Autocomplete request failed: ${res.status}`);
    return [];
  }
  const data = await res.json();
  return data.completions || [];
}
async function setModelState(feature, enable) {
  try {
    const res = await fetch(`${BASE}/manage-model`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ feature, enable })
    });
    if (!res.ok) {
      const txt = await res.text();
      console.error(`Failed to set model state for ${feature}:`, txt);
      return null;
    }
    const data = await res.json();
    console.log(`Model state updated: ${feature} = ${enable ? "ON" : "OFF"}`);
    return data;
  } catch (err) {
    console.error(`Failed to toggle model state for ${feature}:`, err);
    return null;
  }
}

// src/extension.ts
var LANGUAGES = ["python", "javascript", "typescript", "c++", "c"];
var statusBarItem;
var previousChatState;
var previousAutoState;
function updateStatusBar() {
  const config = vscode.workspace.getConfiguration("localAI");
  const chatOn = config.get("enableChat");
  const autoOn = config.get("enableAutocomplete");
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
function removePrefix(completion, before) {
  const suffix = before.slice(-200);
  for (let i = 0; i < suffix.length; i++) {
    if (completion.startsWith(suffix.slice(i))) {
      return completion.slice(suffix.length - i);
    }
  }
  return completion;
}
async function syncModelStates() {
  const config = vscode.workspace.getConfiguration("localAI");
  const chatOn = config.get("enableChat", false);
  const autoOn = config.get("enableAutocomplete", false);
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
var AIInlineCompletionProvider = class {
  async provideInlineCompletionItems(document, position, context, token) {
    const config = vscode.workspace.getConfiguration("localAI");
    if (!config.get("enableAutocomplete")) {
      return [];
    }
    if (token.isCancellationRequested) return [];
    try {
      const beforeRange = new vscode.Range(new vscode.Position(0, 0), position);
      const before = document.getText(beforeRange);
      const afterRange = new vscode.Range(
        position,
        document.positionAt(document.offsetAt(position) + 1e3)
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
};
async function ensureSession() {
  try {
    const sid = await getCurrentSession();
    return sid;
  } catch {
    const sid = await createSession("vscode-session", true);
    return sid;
  }
}
async function callAgent(instruction, code) {
  const config = vscode.workspace.getConfiguration("localAI");
  if (!config.get("enableChat")) {
    vscode.window.showWarningMessage(
      "Chat assistant is disabled. Enable it in the status bar to use this feature.",
      "Enable Now"
    ).then((selection) => {
      if (selection === "Enable Now") {
        vscode.commands.executeCommand("simple-code-agent.toggleSettings");
      }
    });
    return;
  }
  const outputChannel = vscode.window.createOutputChannel("AI Assistant");
  outputChannel.show(true);
  outputChannel.appendLine(`\u{1F9E0} Task: ${instruction}
`);
  const sid = await ensureSession();
  try {
    await streamCode(code || "", instruction, (chunk) => {
      outputChannel.append(chunk);
    }, sid);
  } catch (err) {
    if (err.message.includes("503") || err.message.includes("disabled")) {
      vscode.window.showErrorMessage(
        "Chat assistant is disabled on the backend. Please enable it.",
        "Enable Now"
      ).then((selection) => {
        if (selection === "Enable Now") {
          vscode.commands.executeCommand("simple-code-agent.toggleSettings");
        }
      });
    } else {
      vscode.window.showErrorMessage(`AI Assistant error: ${err.message}`);
    }
  }
}
function activate(context) {
  console.log('Extension "simple-code-agent" is active!');
  const config = vscode.workspace.getConfiguration("localAI");
  previousChatState = config.get("enableChat", false);
  previousAutoState = config.get("enableAutocomplete", false);
  const askAIDisposable = vscode.commands.registerCommand("simple-code-agent.askAgent", async () => {
    const editor = vscode.window.activeTextEditor;
    let code = "";
    if (editor) code = editor.document.getText(editor.selection);
    const instruction = await vscode.window.showInputBox({
      prompt: code ? "What do you want to do with the code?" : "Ask the AI assistant anything about coding",
      value: code ? "Explain this function" : ""
    });
    if (!instruction) return;
    await callAgent(instruction, code);
  });
  const resetDisposable = vscode.commands.registerCommand("simple-code-agent.resetSession", async () => {
    try {
      const sid = await getCurrentSession();
      await resetSession(sid);
      vscode.window.showInformationMessage(`\u2705 AI Assistant memory cleared for session ${sid}`);
    } catch {
      vscode.window.showInformationMessage("No current session to reset. Ask the assistant first to create one.");
    }
  });
  const toggleDisposable = vscode.commands.registerCommand("simple-code-agent.toggleSettings", async () => {
    const config2 = vscode.workspace.getConfiguration("localAI");
    const currentChat = config2.get("enableChat");
    const currentAuto = config2.get("enableAutocomplete");
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
    if (selection === void 0) {
      return;
    }
    const newChatState = selection.some((i) => i.label.includes("Enable Chat Assistant"));
    const newAutoState = selection.some((i) => i.label.includes("Enable Autocomplete"));
    await vscode.window.withProgress({
      location: vscode.ProgressLocation.Notification,
      title: "Updating AI models...",
      cancellable: false
    }, async (progress) => {
      progress.report({ increment: 0, message: "Updating settings..." });
      await config2.update("enableChat", newChatState, vscode.ConfigurationTarget.Global);
      await config2.update("enableAutocomplete", newAutoState, vscode.ConfigurationTarget.Global);
      progress.report({ increment: 50, message: "Syncing with backend..." });
      await setModelState("chat", newChatState);
      await setModelState("autocomplete", newAutoState);
      previousChatState = newChatState;
      previousAutoState = newAutoState;
      progress.report({ increment: 100, message: "Done!" });
      updateStatusBar();
      const chatStatus = newChatState ? "ON \u2713" : "OFF";
      const autoStatus = newAutoState ? "ON \u2713" : "OFF";
      vscode.window.showInformationMessage(
        `AI Updated: Chat ${chatStatus}, Autocomplete ${autoStatus}`
      );
    });
  });
  statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  statusBarItem.command = "simple-code-agent.toggleSettings";
  context.subscriptions.push(statusBarItem);
  syncModelStates();
  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration(async (e) => {
      if (e.affectsConfiguration("localAI")) {
        console.log("Configuration changed, syncing model states...");
        await syncModelStates();
      }
    })
  );
  const inlineProvider = vscode.languages.registerInlineCompletionItemProvider(
    LANGUAGES,
    new AIInlineCompletionProvider()
  );
  context.subscriptions.push(askAIDisposable, resetDisposable, toggleDisposable, inlineProvider);
  console.log("\u2705 AI Assistant extension fully activated");
}
function deactivate() {
  console.log("AI Assistant extension deactivated");
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  activate,
  deactivate
});
//# sourceMappingURL=extension.js.map
