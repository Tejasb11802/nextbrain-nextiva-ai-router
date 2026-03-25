"""
NextBrain Impact Logger
Tracks every query routed through the system and computes time-saved metrics.
Persists to JSON for the dashboard to read.
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
from typing import TypedDict, Optional


class RouteResultDict(TypedDict):
    """Dict-compatible result from the LangGraph workflow."""
    tool: str
    confidence: float
    reasoning: str
    response: str
    time_saved_minutes: int
    timestamp: str
    query: str
    used_llm: bool

LOG_FILE = Path(__file__).parent.parent / "data" / "query_log.json"


def _load_log() -> list:
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_log(log: list):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


def log_query(route_result) -> None:
    """Append a RouteResult (dataclass or dict) to the persistent log."""
    log = _load_log()
    if isinstance(route_result, dict):
        entry = {
            "timestamp": route_result.get("timestamp", datetime.now().isoformat()),
            "query": route_result.get("query", ""),
            "tool": route_result.get("tool", "NED"),
            "confidence": route_result.get("confidence", 0.5),
            "time_saved_minutes": route_result.get("time_saved_minutes", 0),
            "used_llm": route_result.get("used_llm", False),
        }
    else:
        entry = {
            "timestamp": route_result.timestamp,
            "query": route_result.query,
            "tool": route_result.tool,
            "confidence": route_result.confidence,
            "time_saved_minutes": route_result.time_saved_minutes,
            "used_llm": route_result.used_llm,
        }
    log.append(entry)
    _save_log(log)


def get_all_logs() -> list:
    return _load_log()


def get_weekly_stats() -> dict:
    """Compute stats for the past 7 days."""
    log = _load_log()
    cutoff = datetime.now() - timedelta(days=7)

    recent = [
        entry for entry in log
        if datetime.fromisoformat(entry["timestamp"]) >= cutoff
    ]

    if not recent:
        return {
            "total_queries": 0,
            "total_time_saved_hours": 0,
            "tool_breakdown": {},
            "queries_by_day": {},
            "top_tool": None,
            "avg_confidence": 0,
        }

    tool_counts = defaultdict(int)
    tool_time = defaultdict(int)
    queries_by_day = defaultdict(int)
    total_time = 0
    total_confidence = 0

    for entry in recent:
        tool = entry["tool"]
        tool_counts[tool] += 1
        tool_time[tool] += entry["time_saved_minutes"]
        total_time += entry["time_saved_minutes"]
        total_confidence += entry["confidence"]

        day = entry["timestamp"][:10]
        queries_by_day[day] += 1

    top_tool = max(tool_counts, key=tool_counts.get)

    return {
        "total_queries": len(recent),
        "total_time_saved_hours": round(total_time / 60, 1),
        "tool_breakdown": dict(tool_counts),
        "tool_time_saved": dict(tool_time),
        "queries_by_day": dict(sorted(queries_by_day.items())),
        "top_tool": top_tool,
        "avg_confidence": round(total_confidence / len(recent), 2),
    }


def clear_log():
    _save_log([])
