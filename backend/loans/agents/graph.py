import json
import logging
import os

from langchain_core.messages import SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import tools_condition

from ..models import ChatSession
from ..tools import build_tools

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a warm, concise loan assistant. Help the applicant through these steps:
1. Greet them and gather full name, monthly income, and employment type. Accept document OCR text as profile details.
2. Once those details are available, call updateProfile and ask for their 12-digit Aadhaar number and date of birth.
3. Call verifyKYC only when both Aadhaar and date of birth are provided. If verification fails, stop the application and direct them to a branch.
4. After successful KYC, ask for PAN. Call getCreditScore only when they provide it. A score below 600 or a missing record is a final rejection.
5. For a score of 600 or above, call calculateFOIR using the applicant's monthly income and the EMI returned by getCreditScore. FOIR above 50% is a final rejection.
6. When eligible, ask whether they want to see loan options. Only after confirmation call getAvailableLoans and show the returned products.
7. After the applicant chooses one of the returned products, call generateLoanPDF and share its download link.
Never invent record data, loan products, eligibility results, or completed verification. Ask one clear question at a time. Do not reveal full Aadhaar or PAN values in your replies. Use the tools for all database checks and state changes. The tool functions are authoritative; never claim a step succeeded unless its tool result confirms it."""


def make_graph(session_id: str, user_id: int):
    api_key = (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("LLM_API_KEY")
        or os.getenv("GROQ_API_KEY")
        or os.getenv("CEREBRAS_API_KEY")
    )
    if not api_key:
        raise RuntimeError("Configure GEMINI_API_KEY or LLM_API_KEY in backend/.env to enable the loan assistant.")

    base_url = os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
    model = os.getenv("LLM_MODEL", "gemini-2.5-flash")

    llm = ChatOpenAI(model=model, api_key=api_key, base_url=base_url, temperature=0.3)

    tools = build_tools(session_id, user_id)
    llm_with_tools = llm.bind_tools(tools)
    tools_by_name = {item.name: item for item in tools}

    def call_model(state):
        session = ChatSession.objects.get(session_id=session_id, user_id=user_id)
        state_context = {"stage": session.stage, "profile": session.profile, "state": session.state}
        messages = [SystemMessage(content=SYSTEM_PROMPT + "\n\nCurrent application state: " + json.dumps(state_context, default=str))]
        return {"messages": [llm_with_tools.invoke(messages + state["messages"])]}

    def run_tools(state):
        tool_messages = []
        for call in state["messages"][-1].tool_calls:
            try:
                result = tools_by_name[call["name"]].invoke(call["args"])
            except Exception as exc:
                logger.exception("LangGraph tool execution failed: %s", call.get("name"))
                result = {"error": "Tool execution failed. Do not claim the requested action succeeded."}
            tool_messages.append(ToolMessage(content=json.dumps(result, default=str), tool_call_id=call["id"]))
        return {"messages": tool_messages}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", call_model)
    builder.add_node("tools", run_tools)
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    builder.add_edge("tools", "agent")
    return builder.compile()


def reply_for(session_id: str, user_id: int, conversation: list) -> str:
    graph = make_graph(session_id, user_id)
    result = graph.invoke({"messages": conversation}, config={"recursion_limit": 16})
    content = result["messages"][-1].content
    if isinstance(content, str):
        return content
    return "".join(part.get("text", "") for part in content if isinstance(part, dict))
