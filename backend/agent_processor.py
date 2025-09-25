import os, sys, json
import logging
from typing import Generator, List, Dict, Any, Optional

from typing_extensions import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, ToolMessage
from langchain_ollama import ChatOllama


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools import TOOLS

from db import append_messages  # your MongoDB helper that saves messages

log = logging.getLogger("agent_processor")
log.setLevel(logging.INFO)

Message = Dict[str, str]

# Keep your system prompt
SYSTEM_PROMPT = """
You are a helpful AI coding assistant.
Be concise (don't show detail unless asked) and use Markdown for code.
If you want to perform a tool action, you may call the available tools.
"""

llm = ChatOllama(model="qwen2.5-coder:7b", temperature=0)
tool_funcs = [func for _, func in TOOLS.items()]

# Not all model integrations require .bind_tools; ChatOllama supports this pattern.
try:
    model_with_tools = llm.bind_tools(tool_funcs)
except Exception:
    model_with_tools = llm
    log.info(
        "llm.bind_tools not available; proceeding without binding (model may not know tool schemas)."
    )


# --- Graph state definition ---
class AgentState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]


# --- Node implementations ---
def llm_node(state: AgentState) -> dict:
    messages = state.get("messages", [])
    try:
        ai_msg = model_with_tools.invoke(messages)

        # --- Patch: detect JSON tool call in plain content ---
        if isinstance(ai_msg, AIMessage) and isinstance(ai_msg.content, str):
            try:
                data = json.loads(ai_msg.content)
                if isinstance(data, dict) and "name" in data and "arguments" in data:
                    # Convert to a ToolMessage so LangGraph routes correctly
                    tool_msg = ToolMessage(
                        tool_call_id=data.get("id", "call-1"),
                        name=data["name"],
                        content=data.get("arguments", {}),
                    )
                    return {"messages": [ai_msg, tool_msg]}
            except Exception:
                pass  # content wasn’t JSON, just continue

    except Exception as e:
        err_text = f"[LLM error] {type(e).__name__}: {e}"
        log.exception(err_text)
        ai_msg = AIMessage(content=err_text, additional_kwargs={})

    return {"messages": [ai_msg]}


# ToolNode handles executing tools called by the model.
tool_node = ToolNode(tool_funcs)


def route_after_llm(state: AgentState):
    messages = state.get("messages", [])
    if not messages:
        return END

    last = messages[-1]

    # Case 1: model used proper tool_calls
    additional = getattr(last, "additional_kwargs", {}) or {}
    if additional.get("tool_calls") or additional.get("tool_call"):
        return "tools"

    # Case 2: model output already a ToolMessage
    if isinstance(last, ToolMessage):
        return "tools"

    return END


# --- Build and compile the state graph once at import time ---
builder = StateGraph(AgentState)
builder.add_node("llm", llm_node)
builder.add_node("tools", tool_node)

# entry
builder.add_edge(START, "llm")
# If llm produced a tool call, run tools, then go back to llm; otherwise, end
builder.add_conditional_edges("llm", route_after_llm)
# if tools run, run llm again
builder.add_edge("tools", "llm")
# also allow llm->END implicitly if route returns END

compiled = builder.compile()


# --- Helper to extract textual content from message / chunks returned by graph.stream ---
def extract_text_from_msg(msg: AnyMessage) -> str:
    """
    Given a LangChain message or chunk, extract plain text.
    Handles AIMessage with string content, or content blocks list.
    """
    try:
        content = getattr(msg, "content", None)
        if isinstance(content, str):
            return content
        # some message content types are lists of blocks like [{"type":"text", "text":"..."}]
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
                else:
                    parts.append(str(block))
            return "".join(parts)
        # fallback to str()
        return str(content)
    except Exception:
        return str(msg)


def stream_model(
    code: str, instruction: str, memory: List[Message], session_id: str
) -> Generator[str, None, None]:
    """
    Build messages from memory + current user input, run the graph as a compiled runnable,
    stream LLM tokens back to caller, and persist assistant/tool outputs to DB.
    """

    messages_input = []
    messages_input.append(HumanMessage(content=SYSTEM_PROMPT) if False else None)
    messages_input = [HumanMessage(content=SYSTEM_PROMPT)]

    for m in memory:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "assistant":
            messages_input.append(AIMessage(content=content))
        else:
            messages_input.append(HumanMessage(content=content))

    user_prompt = f"Task: {instruction}\n\nCode:\n```text\n{code}\n```"
    messages_input.append(HumanMessage(content=user_prompt))
    append_messages(session_id, "user", user_prompt)

    assistant_accum = ""
    try:
        for msg_or_chunk, metadata in compiled.stream(
            {"messages": messages_input}, stream_mode="messages"
        ):
            # metadata contains 'langgraph_node' and other info; filter LLM tokens by node name ("llm")
            node = metadata.get("langgraph_node")
            # msg_or_chunk can be an AIMessage chunk, ToolMessage chunk, or the full message depending on provider
            text = extract_text_from_msg(msg_or_chunk)
            if not text:
                continue

            # If it's coming from the LLM node, yield it as part of the assistant reply
            if node == "llm":
                assistant_accum += text
                yield text

            # If it's coming from the tools node (tool outputs), persist and also yield so the user sees tool output inline
            elif node == "tools":
                # ToolNode returns ToolMessage(s). Save and surface them.
                tool_output = text
                append_messages(
                    session_id, "assistant", f"[tool output]:\n{tool_output}"
                )
                yield f"\n[tool output]:\n{tool_output}\n"

            else:
                # Other nodes (optional): yield them too (or ignore)
                # yield text
                pass

    except Exception as e:
        err = f"[agent error] {type(e).__name__}: {e}"
        log.exception(err)
        yield err
        append_messages(session_id, "assistant", err)
        return

    if assistant_accum.strip():
        append_messages(session_id, "assistant", assistant_accum)
