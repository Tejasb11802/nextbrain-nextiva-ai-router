"""
NextBrain — Nextiva Internal AI Router
Streamlit UI: Chat interface + Impact Dashboard
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import time
import json
from datetime import datetime

from agent.router import route_query, TOOLS
from utils.logger import log_query, get_weekly_stats, get_all_logs, clear_log

# Try to import LangGraph workflow — use it if available
# Try to import LangGraph workflow — use it if available

import warnings
warnings.filterwarnings("ignore")

LANGGRAPH_AVAILABLE = False
try:
    from langgraph.graph import StateGraph, END
    from agent.workflow import run_workflow
    LANGGRAPH_AVAILABLE = True
except Exception:
    LANGGRAPH_AVAILABLE = False

def process_query(query: str) -> dict:
    """Use LangGraph workflow if available, else simple router."""
    if LANGGRAPH_AVAILABLE:
        state = run_workflow(query)
        return {
            "tool": state.get("tool", "NED"),
            "confidence": state.get("confidence", 0.5),
            "reasoning": state.get("reasoning", ""),
            "response": state.get("final_response", ""),
            "time_saved_minutes": state.get("time_saved_minutes", 0),
            "used_llm": state.get("used_llm", False),
            "clarification_needed": state.get("clarification_needed", False),
            "via_langgraph": True,
        }
    else:
        result = route_query(query)
        log_query(result)
        return {
            "tool": result.tool,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "response": result.response,
            "time_saved_minutes": result.time_saved_minutes,
            "used_llm": result.used_llm,
            "clarification_needed": False,
            "via_langgraph": False,
        }

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NextBrain — Nextiva AI Router",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
  }

  /* Dark background */
  .stApp {
    background: #0A0B0F;
    color: #E8E9F0;
  }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: #0F1018 !important;
    border-right: 1px solid #1E2030;
  }

  /* Main content area */
  .main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
  }

  /* Header */
  .nb-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 2rem;
  }

  .nb-logo {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #FF6B35 0%, #F7C59F 50%, #EFEFD0 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -1px;
  }

  .nb-tagline {
    font-size: 0.8rem;
    color: #6B7280;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.05em;
  }

  /* Tool badge */
  .tool-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.05em;
    border: 1px solid;
  }

  /* Chat messages */
  .chat-user {
    background: #1A1D2E;
    border: 1px solid #2A2D3E;
    border-radius: 12px 12px 4px 12px;
    padding: 12px 16px;
    margin: 8px 0;
    margin-left: 20%;
    color: #E8E9F0;
  }

  .chat-bot {
    background: #0F1118;
    border: 1px solid #1E2130;
    border-radius: 4px 12px 12px 12px;
    padding: 16px;
    margin: 8px 0;
    margin-right: 5%;
    color: #E8E9F0;
  }

  .chat-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    flex-wrap: wrap;
  }

  /* Metric cards */
  .metric-card {
    background: #0F1118;
    border: 1px solid #1E2130;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
  }

  .metric-value {
    font-size: 2.2rem;
    font-weight: 700;
    color: #FF6B35;
    line-height: 1;
  }

  .metric-label {
    font-size: 0.75rem;
    color: #6B7280;
    margin-top: 4px;
    font-family: 'JetBrains Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  /* Confidence bar */
  .conf-bar-bg {
    background: #1E2130;
    border-radius: 4px;
    height: 6px;
    width: 100%;
    margin-top: 4px;
  }

  .conf-bar-fill {
    border-radius: 4px;
    height: 6px;
  }

  /* Input styling */
  .stTextInput > div > div > input {
    background: #0F1118 !important;
    border: 1px solid #2A2D3E !important;
    color: #E8E9F0 !important;
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important;
  }

  .stTextInput > div > div > input:focus {
    border-color: #FF6B35 !important;
    box-shadow: 0 0 0 2px rgba(255,107,53,0.2) !important;
  }

  /* Button */
  .stButton > button {
    background: linear-gradient(135deg, #FF6B35, #FF8C42) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
  }

  .stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(255,107,53,0.4) !important;
  }

  /* Divider */
  hr {
    border-color: #1E2130 !important;
  }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {
    background: #0F1118;
    border-radius: 8px;
    padding: 4px;
    gap: 4px;
  }

  .stTabs [data-baseweb="tab"] {
    color: #6B7280 !important;
    border-radius: 6px !important;
    font-family: 'Space Grotesk', sans-serif !important;
  }

  .stTabs [aria-selected="true"] {
    background: #FF6B35 !important;
    color: white !important;
  }

  /* Tool cards in sidebar */
  .tool-sidebar-card {
    background: #141520;
    border: 1px solid #1E2130;
    border-radius: 8px;
    padding: 10px 12px;
    margin: 6px 0;
    font-size: 0.82rem;
  }

  .tool-name {
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
  }

  .tool-desc {
    color: #6B7280;
    font-size: 0.75rem;
    margin-top: 2px;
  }

  /* Section headers */
  .section-header {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #4B5563;
    font-family: 'JetBrains Mono', monospace;
    margin: 16px 0 8px 0;
    font-weight: 500;
  }

  /* Response markdown */
  .chat-bot table {
    width: 100%;
    border-collapse: collapse;
  }

  .chat-bot th {
    background: #1A1D2E;
    padding: 8px 12px;
    text-align: left;
    font-size: 0.8rem;
    color: #9CA3AF;
  }

  .chat-bot td {
    padding: 8px 12px;
    border-bottom: 1px solid #1E2130;
    font-size: 0.85rem;
  }

  /* Time saved pill */
  .time-pill {
    display: inline-block;
    background: rgba(16,185,129,0.15);
    color: #10B981;
    border: 1px solid rgba(16,185,129,0.3);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.72rem;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 500;
  }

  /* Example query chips */
  .example-chip {
    display: inline-block;
    background: #141520;
    border: 1px solid #2A2D3E;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 0.8rem;
    color: #9CA3AF;
    margin: 3px;
    cursor: pointer;
  }

  /* Scrollable chat area */
  .chat-scroll {
    max-height: 500px;
    overflow-y: auto;
    padding-right: 4px;
  }
</style>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "total_saved" not in st.session_state:
    st.session_state.total_saved = 0


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="nb-logo">🧠 NextBrain</div>', unsafe_allow_html=True)
    st.markdown('<div class="nb-tagline">Nextiva Internal AI Router</div>', unsafe_allow_html=True)
    st.markdown("---")

    # API Key configuration
    st.markdown('<div class="section-header">⚙️ Configuration</div>', unsafe_allow_html=True)
    openai_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...", key="openai_key")
    anthropic_key = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...", key="anthropic_key")

    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
        st.success("✅ OpenAI connected — LLM routing active")
    elif anthropic_key:
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key
        st.success("✅ Claude connected — LLM routing active")
    else:
        st.info("🔧 No API key — using smart rule-based routing")

    st.markdown("---")
    st.markdown('<div class="section-header">🔗 Workflow Engine</div>', unsafe_allow_html=True)
    if LANGGRAPH_AVAILABLE:
        st.success("✅ LangGraph active — 5-node agentic pipeline")
        st.caption("classify → validate → execute → generate → log")
    else:
        st.warning("⚙️ Install LangGraph to enable agentic mode")
        st.code("pip install langgraph langchain\nlangchain-openai langchain-anthropic", language="bash")

    st.markdown("---")

    # Tool directory
    st.markdown('<div class="section-header">🛠️ Nextiva AI Tools</div>', unsafe_allow_html=True)
    for name, config in TOOLS.items():
        st.markdown(f"""
        <div class="tool-sidebar-card">
          <div class="tool-name" style="color:{config['color']}">{config['icon']} {name}</div>
          <div class="tool-desc">{config['use_case']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.session_state.total_saved = 0
        st.rerun()

    if st.button("🔄 Reset Impact Log"):
        clear_log()
        st.success("Log cleared")


# ── Main area ─────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["💬  Chat Router", "📊  Impact Dashboard"])


# ════════════════════════════════════════════════════════
# TAB 1 — CHAT
# ════════════════════════════════════════════════════════
with tab1:
    # Header
    st.markdown("""
    <div class="nb-header">
      <div>
        <div style="font-size:1.6rem;font-weight:700;color:#E8E9F0;">
          What do you need help with?
        </div>
        <div style="font-size:0.85rem;color:#6B7280;margin-top:4px;">
          NextBrain automatically routes your query to the right Nextiva AI tool
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Example queries
    st.markdown('<div class="section-header">Try these examples</div>', unsafe_allow_html=True)
    examples = [
        "Why are we losing deals in the enterprise segment?",
        "Search our internal docs for the onboarding procedure",
        "Build a RAG app from our product knowledge base",
        "What objections came up most in sales calls this month?",
        "Generate an RFP response for the Acme Corp bid",
        "Compare GPT-4 vs Claude for summarization tasks",
        "Show me Q3 win rate trends by region",
    ]

    cols = st.columns(3)
    example_clicked = None
    for i, ex in enumerate(examples):
        if cols[i % 3].button(ex, key=f"ex_{i}", use_container_width=True):
            example_clicked = ex

    st.markdown("---")

    # Chat history display
    if st.session_state.messages:
        st.markdown('<div class="section-header">Conversation</div>', unsafe_allow_html=True)
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-user">👤 {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                result = msg["result"]
                tool_name = result.get("tool", "NED")
                tool_config = TOOLS.get(tool_name, list(TOOLS.values())[0])
                conf_pct = int(result.get("confidence", 0.5) * 100)
                conf_color = "#10B981" if conf_pct >= 80 else "#F59E0B" if conf_pct >= 60 else "#EF4444"
                via_lg = result.get("via_langgraph", False)
                route_label = "🔗 LangGraph" if via_lg else ("🤖 LLM" if result.get("used_llm") else "⚡ Rules")
                clarification = result.get("clarification_needed", False)

                st.markdown(f"""
                <div class="chat-bot">
                  <div class="chat-meta">
                    <span class="tool-badge" style="color:{tool_config['color']};border-color:{tool_config['color']}30;background:{tool_config['color']}10">
                      {tool_config['icon']} {tool_name}
                    </span>
                    <span class="time-pill">⏱ ~{result.get('time_saved_minutes', 0)} min saved</span>
                    <span style="font-size:0.72rem;color:#4B5563;font-family:'JetBrains Mono',monospace;">
                      {route_label}
                    </span>
                    {'<span style="font-size:0.72rem;color:#F59E0B;font-family:JetBrains Mono,monospace;">⚠️ low confidence — asked clarification</span>' if clarification else ''}
                  </div>
                  <div style="font-size:0.72rem;color:#4B5563;margin-bottom:10px;font-family:'JetBrains Mono',monospace;">
                    Confidence: {conf_pct}% — {result.get('reasoning', '')}
                  </div>
                  <div class="conf-bar-bg"><div class="conf-bar-fill" style="width:{conf_pct}%;background:{conf_color}"></div></div>
                </div>
                """, unsafe_allow_html=True)

                # Use Streamlit markdown for the actual response content (renders tables/formatting)
                with st.container():
                    st.markdown(result["response"])

                st.markdown("---")

    # Query input
    query_input = st.text_input(
        "Your query",
        placeholder="e.g. Why did we lose the Acme deal? Search our sales playbook...",
        label_visibility="collapsed",
        key="query_box",
    )

    col_btn, col_info = st.columns([1, 4])
    with col_btn:
        submit = st.button("Route Query →", use_container_width=True)

    # Process query
    active_query = example_clicked or (query_input if submit else None)

    if active_query:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": active_query})

        spinner_msg = "🧠 Running agentic workflow (LangGraph)..." if LANGGRAPH_AVAILABLE else "🧠 Routing query..."
        with st.spinner(spinner_msg):
            time.sleep(0.4)
            result = process_query(active_query)

        # Track session savings
        st.session_state.total_saved += result["time_saved_minutes"]

        # Add bot message
        st.session_state.messages.append({
            "role": "assistant",
            "content": result["response"],
            "result": result,
        })
        st.rerun()

    # Session savings counter
    if st.session_state.total_saved > 0:
        hours = st.session_state.total_saved // 60
        mins = st.session_state.total_saved % 60
        label = f"{hours}h {mins}m" if hours else f"{mins}m"
        st.markdown(f"""
        <div style="text-align:center;padding:16px;background:#0F1118;border:1px solid #1E2130;border-radius:12px;margin-top:16px;">
          <div style="font-size:0.7rem;color:#4B5563;font-family:'JetBrains Mono',monospace;text-transform:uppercase;letter-spacing:0.1em;">
            ⚡ This session saved you approximately
          </div>
          <div style="font-size:2rem;font-weight:700;color:#FF6B35;margin-top:4px;">{label}</div>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════
# TAB 2 — IMPACT DASHBOARD
# ════════════════════════════════════════════════════════
with tab2:
    st.markdown("""
    <div style="margin-bottom:1.5rem;">
      <div style="font-size:1.6rem;font-weight:700;color:#E8E9F0;">Impact Dashboard</div>
      <div style="font-size:0.85rem;color:#6B7280;margin-top:4px;">
        Last 7 days — All queries routed through NextBrain
      </div>
    </div>
    """, unsafe_allow_html=True)

    stats = get_weekly_stats()

    # KPI cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-value">{stats['total_queries']}</div>
          <div class="metric-label">Queries Routed</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-value">{stats['total_time_saved_hours']}h</div>
          <div class="metric-label">Time Saved</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        top = stats.get('top_tool', '—')
        icon = TOOLS[top]['icon'] if top in TOOLS else ''
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-value" style="font-size:1.4rem;">{icon} {top}</div>
          <div class="metric-label">Most Used Tool</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        conf = stats.get('avg_confidence', 0)
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-value">{int(conf*100)}%</div>
          <div class="metric-label">Avg. Routing Confidence</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    if stats["total_queries"] == 0:
        st.info("💡 No queries yet! Head to the Chat Router tab and ask something — your impact stats will appear here.")
    else:
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown('<div class="section-header">Tool Usage Breakdown</div>', unsafe_allow_html=True)
            breakdown = stats.get("tool_breakdown", {})
            for tool, count in sorted(breakdown.items(), key=lambda x: -x[1]):
                config = TOOLS.get(tool, {})
                color = config.get("color", "#6B7280")
                icon = config.get("icon", "")
                pct = int(count / stats["total_queries"] * 100)
                time_saved = stats.get("tool_time_saved", {}).get(tool, 0)

                st.markdown(f"""
                <div style="margin:10px 0;">
                  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                    <span style="font-weight:600;color:{color}">{icon} {tool}</span>
                    <span style="font-size:0.8rem;color:#9CA3AF;">{count} queries · {time_saved}min saved</span>
                  </div>
                  <div class="conf-bar-bg">
                    <div class="conf-bar-fill" style="width:{pct}%;background:{color}"></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

        with col_right:
            st.markdown('<div class="section-header">Daily Query Volume</div>', unsafe_allow_html=True)
            qbd = stats.get("queries_by_day", {})
            if qbd:
                import pandas as pd
                df = pd.DataFrame(list(qbd.items()), columns=["Date", "Queries"])
                df["Date"] = pd.to_datetime(df["Date"])
                df = df.set_index("Date")
                st.bar_chart(df, color="#FF6B35")

        st.markdown("---")
        st.markdown('<div class="section-header">Recent Query Log</div>', unsafe_allow_html=True)
        logs = get_all_logs()[-10:][::-1]
        for entry in logs:
            tool = entry["tool"]
            config = TOOLS.get(tool, {})
            color = config.get("color", "#6B7280")
            icon = config.get("icon", "")
            ts = entry["timestamp"][:16].replace("T", " ")
            conf = int(entry["confidence"] * 100)
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;padding:8px 12px;background:#0F1118;
                        border:1px solid #1E2130;border-radius:8px;margin:4px 0;font-size:0.82rem;">
              <span style="color:{color};font-weight:600;font-family:'JetBrains Mono',monospace;min-width:80px">
                {icon} {tool}
              </span>
              <span style="color:#9CA3AF;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                {entry['query']}
              </span>
              <span style="color:#4B5563;font-family:'JetBrains Mono',monospace;font-size:0.72rem;white-space:nowrap;">
                {conf}% · {ts}
              </span>
            </div>
            """, unsafe_allow_html=True)
