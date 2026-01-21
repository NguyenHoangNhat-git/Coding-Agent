# 🚧 **Work in Progress** – This project is under development

# 🧠 Simple Local AI Coding Assistant

An offline AI coding assistant that runs **locally** and integrates directly into VSCode.  
It uses a FastAPI backend with **LangGraph + Ollama** and a custom VSCode extension to provide code explanations, refactoring suggestions, and tool-augmented developer help — all **without sending code to the cloud**.

---

## ✨ Features

- ⚡ **Runs locally** — keep your code private.
- 📝 **Code selection processing** — highlight code (optional) and ask the AI.
- 🔄 **Streaming responses** with LangGraph.
- 🧠 **Memory** — session history stored in MongoDB.
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

### Clone the repo

```bash
git clone https://github.com/NguyenHoangNhat-git/Coding-Agent.git
cd Coding-Agent
```

### Setup dependencies

```bash
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Pull the models from ollama

Pull mistral(for agent) and qwen(for autocomplete)

```bash
ollama pull mistral:7b
ollama pull qwen2.5-coder:1.5b
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

### Setup the VSCode Extension

```bash
cd ../extension
npm install
```

#### Run

1. Open the `extension` folder in VSCode.
2. Press **F5** -> launch a new **Extension Development Host** window.
3. Press **Ctrl+Shift+P** to search for commands
4. Agent commands:

- Select a piece of code and run `Simple Code Agent: Ask Agent` to ask for explanation or just general questions.
- Run `Simple code agent: Toggle settings` to to turn on/off chat and/or autocomplete model.
- Run `Simple code agent: Reset session` to clear the memory

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
