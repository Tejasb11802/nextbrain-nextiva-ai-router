"""
NextBrain LangGraph Agentic Workflow
Pure LangGraph implementation — no LangChain dependencies.
Compatible with Python 3.14+
"""

import os
import json
import re
from typing import TypedDict, Literal, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END
from agent.router import TOOLS, classify_intent_rules, generate_mock_response
from utils.logger import log_query


# ── Typed State ───────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    query: str
    tool: Optional[str]
    confidence: float
    reasoning: str
    clarification_needed: bool
    clarification_question: str
    tool_output: str
    final_response: str
    time_saved_minutes: int
    used_llm: bool
    error: Optional[str]
    timestamp: str


# ── LLM call (raw API, no LangChain) ─────────────────────────────────────────
def _llm_classify(query: str) -> Optional[tuple]:
    """Call OpenAI or Anthropic directly without LangChain."""
    tool_list = "\n".join([
        f"- {name}: {cfg['description']}"
        for name, cfg in TOOLS.items()
    ])
    prompt = f"""You are an intent classifier for Nextiva's internal AI tools.
Available tools:
{tool_list}

User query: "{query}"

Respond ONLY with JSON, no markdown:
{{"tool": "TOOL_NAME", "confidence": 0.95, "reasoning": "brief reason"}}"""

    # Try OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            import urllib.request
            payload = json.dumps({
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "max_tokens": 100,
            }).encode()
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=payload,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {openai_key}"},
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            text = data["choices"][0]["message"]["content"].strip()
            text = re.sub(r"```json|```", "", text).strip()
            d = json.loads(text)
            return d.get("tool", "NED"), float(d.get("confidence", 0.7)), d.get("reasoning", "")
        except Exception:
            pass

    # Try Anthropic
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            import urllib.request
            payload = json.dumps({
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": prompt}],
            }).encode()
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": anthropic_key,
                    "anthropic-version": "2023-06-01",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            text = data["content"][0]["text"].strip()
            text = re.sub(r"```json|```", "", text).strip()
            d = json.loads(text)
            return d.get("tool", "NED"), float(d.get("confidence", 0.7)), d.get("reasoning", "")
        except Exception:
            pass

    return None


# ── Nodes ─────────────────────────────────────────────────────────────────────
def classify_intent(state: AgentState) -> AgentState:
    result = _llm_classify(state["query"])
    if result:
        tool, confidence, reasoning = result
        used_llm = True
    else:
        tool, confidence, reasoning = classify_intent_rules(state["query"])
        used_llm = False
    if tool not in TOOLS:
        tool, confidence = "NED", 0.4
    return {**state, "tool": tool, "confidence": confidence,
            "reasoning": reasoning, "used_llm": used_llm,
            "timestamp": datetime.now().isoformat()}


def validate_confidence(state: AgentState) -> AgentState:
    if state["confidence"] < 0.50:
        question = (
            f"I want to route you to the right tool for: *\"{state['query']}\"*\n\n"
            "Are you trying to:\n"
            "- 🔍 **Search** existing knowledge/docs?\n"
            "- 📊 **Analyze** sales data or trends?\n"
            "- 📞 **Review** call recordings or deal insights?\n"
            "- ⚡ **Build** a new AI app or workflow?\n"
            "- 📝 **Generate** a proposal or RFP response?\n"
            "- 🤖 **Compare** different AI models?"
        )
        return {**state, "clarification_needed": True, "clarification_question": question}
    return {**state, "clarification_needed": False, "clarification_question": ""}


def should_clarify(state: AgentState) -> Literal["ask_clarification", "execute_tool"]:
    return "ask_clarification" if state.get("clarification_needed") else "execute_tool"


def ask_clarification(state: AgentState) -> AgentState:
    return {**state, "final_response": state["clarification_question"],
            "tool_output": "", "time_saved_minutes": 0}


def execute_tool(state: AgentState) -> AgentState:
    tool_output = generate_mock_response(state["tool"], state["query"])
    return {**state, "tool_output": tool_output,
            "time_saved_minutes": TOOLS[state["tool"]]["time_saved_minutes"]}


def generate_response(state: AgentState) -> AgentState:
    return {**state, "final_response": state["tool_output"]}


def log_impact(state: AgentState) -> AgentState:
    log_query({
        "tool": state["tool"],
        "confidence": state["confidence"],
        "reasoning": state["reasoning"],
        "response": state["final_response"],
        "time_saved_minutes": state["time_saved_minutes"],
        "timestamp": state["timestamp"],
        "query": state["query"],
        "used_llm": state["used_llm"],
    })
    return state


# ── Build Graph ───────────────────────────────────────────────────────────────
def build_workflow():
    graph = StateGraph(AgentState)
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("validate_confidence", validate_confidence)
    graph.add_node("ask_clarification", ask_clarification)
    graph.add_node("execute_tool", execute_tool)
    graph.add_node("generate_response", generate_response)
    graph.add_node("log_impact", log_impact)

    graph.set_entry_point("classify_intent")
    graph.add_edge("classify_intent", "validate_confidence")
    graph.add_conditional_edges("validate_confidence", should_clarify,
        {"ask_clarification": "ask_clarification", "execute_tool": "execute_tool"})
    graph.add_edge("execute_tool", "generate_response")
    graph.add_edge("generate_response", "log_impact")
    graph.add_edge("log_impact", END)
    graph.add_edge("ask_clarification", END)
    return graph.compile()


_workflow = None

def get_workflow():
    global _workflow
    if _workflow is None:
        _workflow = build_workflow()
    return _workflow


def run_workflow(query: str) -> dict:
    initial: AgentState = {
        "query": query, "tool": None, "confidence": 0.0,
        "reasoning": "", "clarification_needed": False,
        "clarification_question": "", "tool_output": "",
        "final_response": "", "time_saved_minutes": 0,
        "used_llm": False, "error": None,
        "timestamp": datetime.now().isoformat(),
    }
    try:
        return get_workflow().invoke(initial)
    except Exception as e:
        return {**initial, "final_response": f"Workflow error: {str(e)}", "error": str(e)}
