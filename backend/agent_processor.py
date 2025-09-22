from typing import Generator, List, Dict, Any
from db import append_messages
import os, sys
import logging

# LangGraph / LangChain imports
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama

# allow importing tools package at project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools import TOOLS  # dict name -> function

log = logging.getLogger("agent_processor")
log.setLevel(logging.INFO)

Message = Dict[str, str]

SYSTEM_PROMPT = """
You are a helpful AI coding assistant.
Be concise (don't show detail unless asked) and use Markdown for code.
If you want to perform a tool action, you may call the available tools.
"""

# --- LLM & agent setup -----------------------------------------------------
llm = ChatOllama(model="qwen2.5-coder:7b", temperature=0)

# pass tool callables - LangGraph will wrap them
tool_funcs = [func for _, func in TOOLS.items()]

# prompt expects `messages` (LangGraph)
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("placeholder", "{messages}"),
    ]
)

agent = create_react_agent(model=llm, tools=tool_funcs, prompt=prompt)


def stream_model(
    code: str, instruction: str, memory: List[Message], session_id: str
) -> Generator[str, None, None]:
    """
    Run LangGraph agent with streaming and save conversation to MongoDB.
    Uses stream_mode="messages" for token-level output.
    """
    user_prompt = f"Task: {instruction}\n\nCode:\n```text\n{code}\n```"
    append_messages(session_id, "user", user_prompt)

    # Build conversation context
    messages_input = [
        SystemMessage(content=SYSTEM_PROMPT),
        *[
            (
                HumanMessage(content=m["content"])
                if m["role"] == "user"
                else AIMessage(content=m["content"])
            )
            for m in memory
        ],
        HumanMessage(content=user_prompt),
    ]

    assistant_reply = ""

    try:
        # Each event is (Message, metadata_dict)
        for msg, metadata in agent.stream(
            {"messages": messages_input}, stream_mode="messages"
        ):
            if isinstance(msg, AIMessage) and msg.content:
                if isinstance(msg.content, str):
                    chunk = msg.content
                else:
                    # handle structured chunks
                    chunk = "".join(
                        block["text"]
                        for block in msg.content
                        if block["type"] == "text"
                    )

                assistant_reply += chunk
                yield chunk  # stream partial output immediately

        # Save final reply
        if assistant_reply.strip():
            append_messages(session_id, "assistant", assistant_reply)

    except Exception as e:
        err = f"[agent error] {type(e).__name__}: {str(e)}"
        yield err
        append_messages(session_id, "assistant", err)
