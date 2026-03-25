# 🧠 NextBrain — Nextiva Internal AI Router

> A lightweight **agentic AI orchestration system** that automatically routes employee queries to the right internal Nextiva AI tool — and tracks the impact with a live dashboard.

Built as a portfolio project targeting Nextiva's **AI Engineer Intern** role. Demonstrates real-world skills in LangGraph agentic workflows, LLM routing, and operational AI tooling.

---

## 🎬 Demo

```
"Why are we losing enterprise deals?" → 📞 MARA (Sales Call Intelligence)
"Search our refund policy docs"       → 🔍 NED  (Internal Knowledge Search)
"Build a RAG app for onboarding"      → ⚡ ZARA (No-Code RAG Builder)
"Generate an RFP for Acme Corp"       → 📝 ROSIE (RFP Automation)
"Compare GPT-4 vs Claude"             → 🤖 GPTiva (Multi-Model Playground)
"Show Q3 win rate by region"          → 📊 CARL (Revenue Intelligence)
```

---

## 🏗️ Architecture

```
User Query
    │
    ▼
┌─────────────────┐
│ classify_intent │  ← OpenAI / Claude / Rule-based fallback
│   (Node 1)      │    Returns: tool name, confidence, reasoning
└────────┬────────┘
         │
         ▼
┌──────────────────────┐
│ validate_confidence  │  ← Confidence threshold check (>= 0.50)
│   (Node 2)           │
└──────────┬───────────┘
           │
     ┌─────┴──────┐
     │            │
   LOW          HIGH
confidence    confidence
     │            │
     ▼            ▼
┌──────────┐  ┌──────────────┐
│   ask_   │  │ execute_tool │  ← Mock responses (swap for real APIs)
│clarify   │  │   (Node 3b)  │
│(Node 3a) │  └──────┬───────┘
└────┬─────┘         │
     │               ▼
     │      ┌─────────────────┐
     │      │generate_response│  ← LLM polish or raw output
     │      │   (Node 4)      │
     │      └──────┬──────────┘
     │             │
     │             ▼
     │      ┌─────────────┐
     └─────►│  log_impact │  ← Persist to JSON, compute time saved
            │   (Node 5)  │
            └──────┬──────┘
                   │
                 [END]
```

### Why LangGraph?
- **Typed state** — every node gets a full AgentState dict, no global variables
- **Conditional edges** — low confidence triggers clarification instead of a bad guess
- **Modular** — swap any node (e.g., replace mock with real Nextiva API) without touching the rest
- **Observable** — every state transition is logged; easy to debug and improve

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agentic Workflow | LangGraph StateGraph |
| LLM Integration | LangChain + OpenAI GPT-4o-mini / Claude Haiku |
| Fallback Routing | Custom keyword scoring engine |
| Frontend | Streamlit |
| Persistence | JSON log with weekly stats aggregation |
| Language | Python 3.10+ |

---

## 🚀 Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/nextbrain.git
cd nextbrain
pip install -r requirements.txt
streamlit run app.py
```

Add your OpenAI or Anthropic key in the sidebar — routing upgrades from rule-based to LLM-powered automatically.

---

## 📁 Project Structure

```
nextbrain/
├── app.py                    # Streamlit UI — Chat + Impact Dashboard
├── requirements.txt
├── agent/
│   ├── router.py             # Intent classifier + mock tool responses
│   └── workflow.py           # LangGraph 5-node agentic pipeline
└── utils/
    └── logger.py             # Query logger + weekly stats
```

---

## 📊 Impact Dashboard

Every query logs: tool used, confidence, time saved, timestamp.
Dashboard shows: total queries, hours saved, tool breakdown, daily volume.

---

## 🔮 Roadmap

- [ ] Slack bot — `/nextbrain your query` from any channel
- [ ] Real Nextiva tool API integrations
- [ ] Multi-turn conversation memory
- [ ] Weekly PDF impact digest

---

## 💡 Why This Matters

Nextiva has 6 powerful internal AI tools. Employees still manually decide which one to use — creating friction and reducing adoption. NextBrain eliminates that overhead and creates an audit trail of AI ROI.

*Built by **Tejas Bhanushali** — MS Data Science, Arizona State University*
*Targeting: AI Engineer Intern @ Nextiva, Scottsdale AZ*
