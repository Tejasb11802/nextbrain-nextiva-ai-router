"""
NextBrain Router Agent
Classifies user queries and routes them to the appropriate Nextiva AI tool simulation.
Uses OpenAI or Claude API when keys are available, falls back to rule-based routing.
"""

import os
import re
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

# Tool definitions — mirrors Nextiva's internal AI stack
TOOLS = {
    "ZARA": {
        "description": "No-code RAG app builder for internal knowledge bases",
        "keywords": ["build", "rag", "knowledge base", "document", "create app", "no-code", "ingest", "upload docs"],
        "icon": "⚡",
        "color": "#FF6B35",
        "use_case": "Build & query internal knowledge apps",
        "time_saved_minutes": 45,
    },
    "NED": {
        "description": "Internal knowledge search — find answers across all company docs instantly",
        "keywords": ["find", "search", "where is", "what is our", "policy", "internal", "docs", "knowledge", "look up", "procedure"],
        "icon": "🔍",
        "color": "#4ECDC4",
        "use_case": "Search internal knowledge & docs",
        "time_saved_minutes": 20,
    },
    "MARA": {
        "description": "Sales call intelligence — analyze recordings, surface insights, find patterns",
        "keywords": ["sales call", "call recording", "deal", "won", "lost", "why did", "prospect", "customer said", "objection", "pipeline", "win rate"],
        "icon": "📞",
        "color": "#A855F7",
        "use_case": "Sales call analysis & insights",
        "time_saved_minutes": 60,
    },
    "CARL": {
        "description": "Sales intelligence — win/loss analysis, deal insights, revenue trends",
        "keywords": ["win loss", "revenue", "q3", "q4", "quarter", "forecast", "churn", "closed", "opportunity", "account", "trend", "insight"],
        "icon": "📊",
        "color": "#F59E0B",
        "use_case": "Revenue & sales analytics",
        "time_saved_minutes": 50,
    },
    "ROSIE": {
        "description": "RFP automation — auto-generate proposal responses from past wins",
        "keywords": ["rfp", "proposal", "bid", "response", "procurement", "vendor", "questionnaire", "requirements document"],
        "icon": "📝",
        "color": "#10B981",
        "use_case": "RFP & proposal automation",
        "time_saved_minutes": 240,
    },
    "GPTiva": {
        "description": "Multi-model playground — compare ChatGPT, Claude, and internal LLMs side by side",
        "keywords": ["compare", "gpt", "claude", "model", "which ai", "better response", "test prompt", "llm", "chatgpt", "anthropic"],
        "icon": "🤖",
        "color": "#6366F1",
        "use_case": "Compare & test AI models",
        "time_saved_minutes": 15,
    },
}


@dataclass
class RouteResult:
    tool: str
    confidence: float
    reasoning: str
    response: str
    time_saved_minutes: int
    timestamp: str
    query: str
    used_llm: bool


def classify_intent_rules(query: str) -> tuple[str, float, str]:
    """Rule-based fallback classifier using keyword matching with scoring."""
    query_lower = query.lower()
    scores = {}

    for tool, config in TOOLS.items():
        score = 0
        matched_keywords = []
        for kw in config["keywords"]:
            if kw in query_lower:
                score += 1
                matched_keywords.append(kw)
        if score > 0:
            scores[tool] = (score, matched_keywords)

    if not scores:
        return "NED", 0.4, "No specific keywords matched — defaulting to NED for general knowledge search."

    best_tool = max(scores, key=lambda t: scores[t][0])
    best_score, matched = scores[best_tool]
    total_keywords = len(TOOLS[best_tool]["keywords"])
    confidence = min(0.95, 0.5 + (best_score / total_keywords) * 0.5)
    reasoning = f"Matched keywords: {', '.join(matched)}"
    return best_tool, confidence, reasoning


def classify_intent_llm(query: str) -> Optional[tuple[str, float, str]]:
    """Use OpenAI or Claude to classify intent if API key is available."""
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    tool_list = "\n".join([
        f"- {name}: {config['description']} (use for: {', '.join(config['keywords'][:4])})"
        for name, config in TOOLS.items()
    ])

    prompt = f"""You are an intent classifier for Nextiva's internal AI tools.

Available tools:
{tool_list}

User query: "{query}"

Respond with ONLY a JSON object like:
{{"tool": "TOOL_NAME", "confidence": 0.95, "reasoning": "brief reason"}}

Pick the single best tool. No other text."""

    try:
        if openai_key:
            import openai
            client = openai.OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=150,
            )
            text = response.choices[0].message.content.strip()
            import json
            data = json.loads(text)
            return data["tool"], data["confidence"], data["reasoning"]

        elif anthropic_key:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            import json
            data = json.loads(text)
            return data["tool"], data["confidence"], data["reasoning"]

    except Exception:
        return None

    return None


def generate_mock_response(tool: str, query: str) -> str:
    """Generate realistic mock responses for each tool."""
    responses = {
        "ZARA": f"""✅ **ZARA — RAG App Builder**

I can help you build a no-code RAG application for: *"{query}"*

**Suggested setup:**
- 📂 **Data source:** Upload PDFs, Confluence pages, or Google Docs
- 🔗 **Embedding model:** text-embedding-ada-002 (recommended)
- 🧠 **Retrieval:** Top-5 semantic chunks with MMR diversity
- 💬 **Interface:** Auto-generated chat UI, shareable link in 2 minutes

**Next step:** Click "New App" → drag & drop your documents → ZARA handles chunking, indexing, and deployment automatically.

*Estimated setup time: 8 minutes vs ~3 hours manual setup*""",

        "NED": f"""🔍 **NED — Internal Knowledge Search**

Searching across Nextiva's internal knowledge base for: *"{query}"*

**Top results found:**
1. 📄 **Internal Playbook v2.3** — Section 4.2 (92% match)
   > "...standard operating procedure for this use case is documented in the GTM handbook..."
2. 📄 **Confluence: Engineering Wiki** — AI Ops Team Page (87% match)
   > "...refer to the onboarding checklist and tool access guide..."
3. 📄 **Slack Archive: #ai-ops channel** — 3 days ago (81% match)
   > "...Kevin shared the updated workflow doc in the pinned messages..."

*Found in 1.2 seconds. Manual search estimate: ~18 minutes*""",

        "MARA": f"""📞 **MARA — Sales Call Intelligence**

Analyzed 847 recorded calls for patterns related to: *"{query}"*

**Key Insights:**
- 🔴 **Top objection (38% of lost deals):** Pricing concerns raised before value demo
- 🟢 **Win pattern:** Reps who mentioned ROI in first 5 min closed at 2.3x rate
- 📈 **Trending topic this week:** Integration with existing CRM tools (+22%)
- ⚡ **Recommended talk track:** Lead with the 3-minute ROI calculator demo

**Suggested action:** Share the "pricing objection" battlecard with your team — it cut churn in this segment by 18% last quarter.

*Analyzed in 4 seconds vs ~6 hours manual review*""",

        "CARL": f"""📊 **CARL — Revenue & Sales Intelligence**

Running analysis for: *"{query}"*

**Dashboard Summary:**
| Metric | This Quarter | vs Last Quarter |
|--------|-------------|-----------------|
| Win Rate | 34% | ▲ +7% |
| Avg Deal Size | $12,400 | ▲ +12% |
| Pipeline Coverage | 3.2x | ▼ -0.4x |
| Churn Rate | 4.1% | ▼ -1.2% |

**AI Insight:** Enterprise segment is outperforming SMB by 2.1x — recommend shifting 20% of outbound effort to 200-500 employee companies based on current win patterns.

*Generated in 6 seconds vs ~4 hours manual reporting*""",

        "ROSIE": f"""📝 **ROSIE — RFP Automation**

Processing request for: *"{query}"*

**Auto-generated proposal sections:**
- ✅ Executive Summary — pulled from 12 winning proposals (94% similarity match)
- ✅ Technical Architecture — matched to RFP requirements section 3.1-3.4
- ✅ Security & Compliance — SOC2, GDPR clauses auto-inserted
- ✅ Pricing Table — populated from approved rate card
- ⚠️ Custom Integration section — needs 15-min human review

**Status:** Draft ready in Confluence. Estimated completion with review: **2.5 hours**
*Previous manual process: 2-3 weeks*""",

        "GPTiva": f"""🤖 **GPTiva — Multi-Model Comparison**

Running your prompt through 3 models for: *"{query}"*

**Results:**
| Model | Response Quality | Speed | Cost/1K tokens |
|-------|-----------------|-------|----------------|
| GPT-4o | ⭐⭐⭐⭐⭐ | 1.8s | $0.005 |
| Claude 3.5 Sonnet | ⭐⭐⭐⭐⭐ | 1.2s | $0.003 |
| Nextiva Internal LLM | ⭐⭐⭐⭐ | 0.4s | $0.000 |

**Recommendation:** For this use case, Claude 3.5 Sonnet gives the best quality/cost ratio. For high-volume internal tasks, the Nextiva internal model is 4x faster at no cost.

*Saves you from manually testing each model separately*""",
    }
    return responses.get(tool, f"Tool {tool} processed your query: {query}")


def route_query(query: str) -> RouteResult:
    """Main routing function — classify intent and return full result."""
    # Try LLM classification first
    llm_result = classify_intent_llm(query)
    used_llm = False

    if llm_result:
        tool, confidence, reasoning = llm_result
        used_llm = True
    else:
        tool, confidence, reasoning = classify_intent_rules(query)

    # Validate tool name
    if tool not in TOOLS:
        tool = "NED"
        confidence = 0.4

    response = generate_mock_response(tool, query)
    time_saved = TOOLS[tool]["time_saved_minutes"]

    return RouteResult(
        tool=tool,
        confidence=confidence,
        reasoning=reasoning,
        response=response,
        time_saved_minutes=time_saved,
        timestamp=datetime.now().isoformat(),
        query=query,
        used_llm=used_llm,
    )
