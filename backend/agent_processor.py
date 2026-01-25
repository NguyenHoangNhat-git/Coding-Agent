import os, sys, logging
from typing import Generator, List, Dict, Sequence
from typing_extensions import TypedDict, Annotated

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_ollama import ChatOllama
from db import append_messages

from models_manager import get_chat_model, is_chat_enabled

# Local imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools import TOOLS

# Logging setup
log = logging.getLogger("agent_processor")
log.setLevel(logging.INFO)

Message = Dict[str, str]

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = """
You are an advanced local Coding Assistant running inside VSCode. 
You have access to the user's local file system and terminal.

### Goal
Help the user write code, debug issues, and explore their repository efficiently.

### Available Tools
{tools}

### Rules
1. **Directness:** If you can answer without a tool, do so immediately.
2. **Verification:** Do not guess file paths. Use `list_directory` to check before reading.
3. **Tool Usage:** Call tools directly when needed. Do not explain that you are going to use a tool. Just use it.
4. **Safety:** Warn the user before running destructive terminal commands.
"""


tools = [func for func in TOOLS.values()]


# --- Format tool descriptions for prompt ---
def format_tools_description() -> str:
    return "\n".join(
        f"- {name}: {func.__doc__ or 'No description'}" for name, func in TOOLS.items()
    )


# --- Agent State ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


# --- Agent Node ---
def agent_node(state: AgentState) -> AgentState:
    messages = state["messages"]

    llm = get_chat_model()

    if llm is None:
        error_msg = (
            "Chat assistant is currently disabled. Please enable it in VSCode settings."
        )
        log.warning(error_msg)
        return {"messages": [AIMessage(content=f"❌ {error_msg}")]}

    try:
        llm_with_tools = llm.bind_tools(tools)
        response = llm_with_tools.invoke(messages)

        return {"messages": [response]}
    except Exception as e:
        err = f"[Agent error] {type(e).__name__}: {e}"
        log.exception(err)
        return {"messages": [AIMessage(content=err)]}


# --- Conditional route after agent ---
def route_after_agent(state: AgentState):
    messages = state["messages"]
    if not messages:
        return END

    last = messages[-1]
    # Check if last message has tool calls
    if isinstance(last, AIMessage) and last.tool_calls:
        log.info(f"Routing to tools: {[tc.get('name') for tc in last.tool_calls]}")
        return "tools"

    return END


# --- Tool Node ---
tool_node = ToolNode([func for _, func in TOOLS.items()])

# --- Build Graph ---
builder = StateGraph(AgentState)

builder.add_node("agent", agent_node)
builder.add_node("tools", tool_node)

builder.set_entry_point("agent")
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", route_after_agent, {"tools": "tools", END: END})
builder.add_edge("tools", "agent")

agent = builder.compile()

# Draw the graph of the agent
try:
    if not os.path.exists("agent_graph.png"):
        png_bytes = agent.get_graph().draw_mermaid_png()
        with open("agent_graph.png", "wb") as f:
            f.write(png_bytes)
        log.info("Agent graph created: agent_graph.png")
except Exception as e:
    log.warning(f"Could not create graph visualization: {e}")


# --- Helpers ---
def extract_text_from_msg(msg: BaseMessage) -> str:
    if isinstance(msg.content, str):
        return msg.content
    elif isinstance(msg.content, list):
        return "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in msg.content
        )
    return str(msg.content)


def build_message_history(memory: List[Message]) -> List[BaseMessage]:
    """Convert memory dict format to LangChain message objects."""
    messages = []
    for m in memory:
        role, content = m.get("role", "user"), m.get("content", "")
        if role == "assistant":
            messages.append(AIMessage(content=content))
        elif role == "system":
            messages.append(SystemMessage(content=content))
        else:
            messages.append(HumanMessage(content=content))
    return messages


# --- Streaming execution ---
def stream_model(
    code: str, instruction: str, memory: List[Message], session_id: str
) -> Generator[str, None, None]:
    """
    Stream agent responses and tool outputs.
    Checks if chat is enabled before processing.
    """

    if not is_chat_enabled():
        error_msg = "❌ Chat assistant is currently disabled. Please enable it in VSCode settings."
        log.warning("Attempted to use chat while disabled")
        yield error_msg
        append_messages(session_id, "assistant", error_msg)
        return

    system_prompt = SYSTEM_PROMPT.format(tools=format_tools_description())
    messages_input = [SystemMessage(content=system_prompt)]
    messages_input.extend(build_message_history(memory))

    user_prompt = (
        f"Task: {instruction}\n\nCode:\n```\n{code}\n```" if code else instruction
    )
    messages_input.append(HumanMessage(content=user_prompt))
    append_messages(session_id, "user", user_prompt)

    full_response = ""

    try:
        for msg, meta in agent.stream(
            {"messages": messages_input}, stream_mode="messages"
        ):
            node = meta.get("langgraph_node")
            text = extract_text_from_msg(msg)
            if not text:
                continue

            # Stream assistant replies
            if node == "agent" and isinstance(msg, AIMessage):
                # Don't stream tool call declarations, only actual content
                if not msg.tool_calls:
                    yield text
                    full_response += text
                else:
                    log.info(
                        f"Agent calling tools: {[tc.get('name') for tc in msg.tool_calls]}"
                    )

            # Stream tool outputs inline
            elif node == "tools":
                tool_output = f"\n [Tool output]: {text}\n"
                yield tool_output
                append_messages(session_id, "assistant", tool_output)

    except Exception as e:
        err = f"[Agent error] {type(e).__name__}: {e}"
        log.exception(err)
        yield f"\n❌ {err}\n"
        append_messages(session_id, "assistant", err)

    if full_response.strip():
        append_messages(session_id, "assistant", full_response)
    else:
        log.warning("No response content was generated")
