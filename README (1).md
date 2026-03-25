# 🧠 NextBrain — Nextiva Internal AI Router

> A lightweight AI orchestration agent that automatically routes queries to the right Nextiva AI tool (ZARA, NED, MARA, CARL, ROSIE, GPTiva) and tracks impact with a live dashboard.

Built as a portfolio project to demonstrate AI engineering skills for Nextiva's AI Engineer Intern role.

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
streamlit run app.py
```

### 3. (Optional) Add API keys in the sidebar
- **OpenAI key** → enables GPT-4o-mini for smarter intent classification
- **Anthropic key** → enables Claude Haiku for routing
- Without keys: runs on fast rule-based routing (still works great for demo)

---

## 🛠️ Architecture

```
nextbrain/
├── app.py                  # Streamlit UI (Chat + Dashboard)
├── agent/
│   └── router.py           # Intent classifier + tool router
├── utils/
│   └── logger.py           # Query logger + weekly stats
├── data/
│   └── query_log.json      # Persisted query history (auto-created)
└── requirements.txt
```

### How routing works
1. User types a query
2. If API key present → Claude/GPT classifies intent → returns tool name + confidence
3. If no key → keyword scoring across all 6 tool definitions
4. Router generates a realistic mock response from the selected tool
5. Query + time-saved is logged to `data/query_log.json`
6. Dashboard auto-updates with new stats

---

## 🤖 Nextiva AI Tools Simulated

| Tool | Purpose | Est. Time Saved |
|------|---------|-----------------|
| ⚡ ZARA | No-code RAG app builder | 45 min/query |
| 🔍 NED | Internal knowledge search | 20 min/query |
| 📞 MARA | Sales call intelligence | 60 min/query |
| 📊 CARL | Revenue & win/loss analytics | 50 min/query |
| 📝 ROSIE | RFP automation | 240 min/query |
| 🤖 GPTiva | Multi-model comparison | 15 min/query |

---

## 📈 Impact Dashboard

The dashboard shows:
- Total queries routed (last 7 days)
- Total hours saved
- Most-used tool
- Average routing confidence
- Tool breakdown with time saved per tool
- Daily query volume chart
- Recent query log

---

## 🔮 Roadmap (Phase 2)
- [ ] Slack bot integration — `/nextbrain what is our refund policy?`
- [ ] Real Nextiva tool API integrations (when access granted)
- [ ] Weekly email digest with impact report
- [ ] Team usage analytics (multi-user tracking)
- [ ] LangGraph multi-step agentic workflows

---

## 💡 Why This Matters for Nextiva

Nextiva has 6 powerful internal AI tools — but employees still have to manually decide which tool to use for each query. NextBrain eliminates that decision overhead and creates an audit trail of AI adoption and ROI, directly supporting Kevin's AI Ops team mission.

*Built by Tejas Bhanushali — MS Data Science, Arizona State University*
