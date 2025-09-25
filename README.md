# 🚧 **Work in Progress** – This project is under active development. Expect breaking changes and incomplete functionality.

# 🧠 Simple Local AI Coding Assistant

An offline AI coding assistant that runs **locally** and integrates directly into VSCode.  
It uses a FastAPI backend with **LangGraph + Ollama** (Qwen2.5 7B by default) and a custom VSCode extension to provide code explanations, refactoring suggestions, and tool-augmented developer help — all **without sending code to the cloud**.

---

## ✨ Features

- ⚡ **Runs locally** — keep your code private.
- 📝 **Code selection processing** — highlight code (optional) and ask the AI.
- 🔄 **Streaming responses** with LangGraph.
- 🧠 **Memory** — per-session history stored in MongoDB.
- 🛠 **Tool support** — the agent can call functions (list files, run commands, etc.).
- 🖥 **VSCode integration** via a custom extension.
- 🧩 Easily switch models (Qwen, CodeLlama, etc.).

---

## 📂 Project Structure

```
project-root/
│
├── backend/                     # FastAPI + LangGraph server
│   ├── main.py                  # API endpoints
│   ├── agent_processor.py       # LangGraph agent (LLM + tools + memory)
│   ├── tools/                   # Custom tool implementations
│   ├── db.py                    # MongoDB helper for memory
│   └── ...
│
├── extension/                   # VSCode extension
│   ├── src/
│   │   ├── extension.ts         # Main extension activation
│   │   ├── apiClient.ts         # Connects to backend API
│   │   └── ...
│   ├── package.json
│   └── tsconfig.json
│
├── requirements.txt             # Python dependencies
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

### 1️⃣ Clone the repo

```bash
git clone https://github.com/NguyenHoangNhat-git/Coding-Agent.git
cd Coding-Agent
```

### 2️⃣ Setup Python Backend

```bash
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

#### Run MongoDB

```bash
sudo systemctl start mongod
```

#### Run the FastAPI server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

API is available at `http://localhost:8000`.

---

### 3️⃣ Setup the VSCode Extension

```bash
cd ../extension
npm install
```

#### Run in Development Mode

1. Open the `extension` folder in VSCode.
2. Press **F5** — this launches a new **Extension Development Host** window.
3. In that new window, open any file, select code, press **Ctrl+Shift+P**, run `Simple Code Agent: Ask Agent`, and edit your prompt.

---

## 🧠 Memory

- Each VSCode session has a unique ID and its own history.
- Conversation history is stored in MongoDB.
- Memory resets if you restart the backend or use **Reset Session** from the extension.

---

## ⚙️ Configuration

- Change **default model** in `backend/agent_processor.py` (`ChatOllama(model="...")`).
- Add or modify **tools** in `backend/tools/`.
- Adjust **default system prompt** in `backend/agent_processor.py`.

---

## 🛠 Requirements

- Python 3.9+
- Node.js 18+
- Ollama
- MongoDB
- VSCode
