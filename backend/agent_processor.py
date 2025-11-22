import os, sys, json, logging, re
from typing import Generator, List, Dict, Sequence
from typing_extensions import TypedDict, Annotated

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_ollama import ChatOllama

# Local imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools import TOOLS
from db import append_messages

# Logging setup
log = logging.getLogger("agent_processor")
log.setLevel(logging.INFO)

Message = Dict[str, str]

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = """
You are a coding assistant integrated inside VSCode.

Your primary goal is to give direct, helpful answers. 
Tools exist ONLY for tasks that cannot be answered directly (e.g., running code, searching the web, reading files, executing terminal commands, etc).

### Rules for Tool Usage
- DO NOT use a tool if the answer can be given directly.
- Use tools ONLY when the user explicitly asks for external information or an action.
- Never guess tool names.
- Never call a tool unless you are 100%% sure it is required.

### Format for Tool Calls
When (and ONLY when) a tool is actually needed, respond with:

Thought: reasoning about why a tool is required  
Action: tool_name  
Action Input: {{"param": "value"}}

Wait for the observation, then continue reasoning.

### Final Answers
When not using tools, reply normally:

Final Answer: <your Markdown response>

### Additional Guidelines
- Be concise and focused.
- Avoid unnecessary explanations.
- Never trigger tools automatically.
- If unsure whether a tool is needed, prefer giving a direct response.
- Treat tool calls as a last resort.

Available tools:
{tools}
"""

# --- Model ---
tools = [func for func in TOOLS.values()]
llm = ChatOllama(model="mistral:7b", temperature=0).bind_tools(tools)
# tested for llama3.2,


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
    try:
        response = llm.invoke(messages)
        # return the full model message object (don't reconstruct)
        return {"messages": [response]}
    except Exception as e:
        err = f"[Agent error] {type(e).__name__}: {e}"
        log.exception(err)
        return {"messages": [AIMessage(content=err)]}


# --- Conditional route after agent ---
def route_after_agent(state: AgentState):
    messages = state["messages"]
    if not messages:
        return "end"

    last = messages[-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return "end"


# --- Tool Node ---
tool_node = ToolNode([func for _, func in TOOLS.items()])

# --- Build Graph ---
builder = StateGraph(AgentState)

builder.add_node("agent", agent_node)
builder.add_node("tools", tool_node)

builder.set_entry_point("agent")
builder.add_edge(START, "agent")
builder.add_conditional_edges(
    "agent", route_after_agent, {"tools": "tools", "end": END}
)
builder.add_edge("tools", "agent")

agent = builder.compile()


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
    """Stream agent responses and tool outputs."""
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
            if node == "agent":
                yield text
                full_response += text

            # Stream tool outputs inline
            elif node == "tools":
                yield f"\n[Tool output]: {text}\n"
                append_messages(session_id, "assistant", f"[Tool output]: {text}")

    except Exception as e:
        err = f"[Agent error] {type(e).__name__}: {e}"
        log.exception(err)
        yield f"\n❌ {err}\n"
        append_messages(session_id, "assistant", err)

    if full_response.strip():
        append_messages(session_id, "assistant", full_response)
