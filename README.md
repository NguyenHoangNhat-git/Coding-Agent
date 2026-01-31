# Simple Local AI Coding Assistant

An offline AI coding assistant that runs **locally** and integrates directly into VSCode.  
It uses a FastAPI backend with **LangGraph + Ollama** and a custom VSCode extension to provide code explanations, refactoring suggestions, and tool-augmented developer help — all **without sending code to the cloud**.

---

## ✨ Features

- **Runs locally** — keep your code private.
- **Code selection processing** — highlight code (optional) and ask the AI.
- **Streaming responses** with LangGraph.
- **Memory** — session history stored in MongoDB.
- **Tool support** — the agent can call functions (list files, run commands, etc.).
- **VSCode integration** via a custom extension.

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

### Clone the repo

```bash
git clone https://github.com/NguyenHoangNhat-git/Coding-Agent.git
cd Coding-Agent
```

### Pull the models from Ollama

```bash
ollama pull mistral:7b
ollama pull qwen2.5-coder:1.5b
```

### Start the backend with Docker

```bash
cd backend
docker compose up -d
```

The API is available at `http://localhost:8000`.

- Stop backend

```bash
cd backend
docker compose down
```

### Setup the VSCode Extension

```bash
npm install
```

#### Run

1. Open the project in VSCode
2. Press **F5** to launch a new Extension Development Host window
3. Use the status bar (bottom-right) to toggle models on/off
4. Press **Ctrl+Shift+P** and search for commands:
   - `Simple Code Agent: Ask Agent` — Ask questions about code
   - `Simple Code Agent: Toggle Settings` — Enable/disable models
   - `Simple Code Agent: Reset Session` — Clear memory

---

## ⚙️ Configuration

- Change **default models** in `backend/models_manager.py`.
- Add or modify **tools** in `backend/tools/`.
- Adjust **default system prompt** in `backend/agent_processor.py`.

---

## 🛠 Requirements

- Python 3.9+
- Node.js 18+
- Ollama
- MongoDB
- VSCode
- Docker

## Docker Commands

Start services:

```bash
docker compose up -d
```

Stop services:

```bash
docker compose down
```

View logs:

```bash
docker compose logs -f
```

Rebuild after changes:

````bash
docker compose up -d --build
```"
```
````
