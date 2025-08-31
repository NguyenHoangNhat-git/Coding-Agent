# 🧠 Simple Local AI Coding Assistant

An offline AI coding assistant that runs **locally** and integrates directly into VSCode.  
It uses a FastAPI backend with a local LLM (e.g., Qwen2.5 7B by default) and a custom VSCode extension to provide code explanations, refactoring suggestions, and other developer tools **without sending code to the cloud**.

---

## ✨ Features

- ⚡ **Runs locally** — keep your code private.
- 📝 **Code selection processing** — highlight code and ask the AI anything.
- 🔄 **Streaming responses** for real-time feedback.
- 🧠 **Short-term memory** — remembers previous interactions in a session.
- 🖥 **VSCode integration** via a custom extension.
- 🧩 Easily switch to different LLMs (CodeLlama, Qwen, etc.).

---

## 📂 Project Structure

```
project-root/
│
├── backend/                 # FastAPI server
│   ├── main.py               # API endpoints for code processing
│   ├── .env.example          # Example environment variables
│   └── ...
│
├── extension/                # VSCode extension
│   ├── src/
│   │   ├── extension.ts      # Main extension activation code
│   │   ├── apiClient.ts      # Connects to backend API
│   │   └── ...
│   ├── package.json
│   ├── tsconfig.json
│   └── ...
│
├── requirements.txt      # Python dependencies
├── .gitignore
├── README.md
└── LICENSE
```

---

## 🚀 Getting Started

### 1️⃣ Clone the repo

```bash
git clone https://github.com/NguyenHoangNhat-git/Coding-Agent.git
cd Coding Agent
```

---

```bash
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2️⃣ Setup the Backend

#### Run the backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Your API will be available at `http://localhost:8000`.

---

### 3️⃣ Setup the VSCode Extension

```bash
cd ../extension
npm install
# may have to run 'npm run watch' or 'npm run compile' if you modify sth
```

#### Run in Development Mode

1. Open the `extension` folder in VSCode.
2. Press **F5** — this launches a new **Extension Development Host** window.
3. In that new window, open any code file, select some code, press **Ctrl+Shift+P**, run `Simple Code Agent: Explain Code` -> Edit the prompt.

---

## 🧠 Memory

- This project now supports short-term memory for conversations.

- Each session (session_id="default" by default) maintains its own history of user prompts and AI responses (check `backend/memory.py` to change default limits).

- You can extend this later to support multiple conversations or users by changing the session_id passed from the extension.

- Memory currently lives in RAM and resets when the backend restarts.

---

## ⚙️ Configuration

You can change:

- **Backend model** (e.g., CodeLlama, Qwen) in `backend/main.py`.
- **Default prompt** in `extension/src/extension.ts`.

---

## 🛠 Requirements

- Python 3.9+
- Node.js 18+
- Ollama
- VSCode
