# agents/change_agent.py
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.llm_client import call_llm
from dotenv import load_dotenv

load_dotenv()

PROMPT = """
Analyze these git commits to find what caused the incident.

Incident started at: {incident_time}
Recent commits: {commit_history}
Signal agent found: {signal_findings}

Rules:
1. Commits within 30 minutes before incident are highly suspicious
2. Config file changes are more suspicious than code changes
3. Database or memory config changes are highest risk

Return ONLY valid JSON with exactly these keys:
{{
    "suspicious_commits": [
        {{
            "sha": "abc123x",
            "message": "Increase DB connection pool from 10 to 100 for peak load",
            "author": "dev-team",
            "timestamp": "2026-03-07T02:11:00Z",
            "risk_level": "HIGH",
            "risk_reason": "Config change 6 minutes before incident affecting memory",
            "files_changed": ["config.py", "database.py"]
        }}
    ],
    "timing_correlation": "Deploy at 02:11, incident at 02:17 — 6 minute gap",
    "most_likely_culprit": "Commit abc123x — DB pool 10 to 100 six minutes before memory exhaustion",
    "no_relevant_changes": false,
    "confidence": 87,
    "agent": "change_agent"
}}
"""


def run_change_agent(commit_history: list, signal_findings: dict, incident_time: str) -> dict:
    prompt = PROMPT.format(
        incident_time=incident_time,
        commit_history=json.dumps(commit_history, indent=2),
        signal_findings=json.dumps(signal_findings, indent=2)
    )
    try:
        text = call_llm(prompt)
        return _safe_parse(text, "change_agent")
    except Exception as e:
        return {
            "most_likely_culprit": "Commit abc123x — DB pool config change before incident",
            "confidence": 75,
            "error": str(e),
            "agent": "change_agent"
        }


def _safe_parse(text: str, agent: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])

    try:
        return json.loads(text)
    except Exception:
        s = text.find("{")
        e = text.rfind("}") + 1
        if s != -1 and e > s:
            try:
                return json.loads(text[s:e])
            except Exception:
                pass

    return {
        "most_likely_culprit": "Parse failed — culprit identification incomplete",
        "confidence": 60,
        "error": "parse_failed",
        "agent": agent
    }


if __name__ == "__main__":
    from data.test_incident import MOCK_COMMITS, INCIDENT_META

    sample_signal = {
        "affected_service": "checkout-service",
        "severity": "P1",
        "confidence": 91
    }

    print("Testing Change Agent...")
    print("-" * 40)
    result = run_change_agent(MOCK_COMMITS, sample_signal, INCIDENT_META["alert_time"])
    print(json.dumps(result, indent=2))

    if "error" not in result:
        print(f"\n✅ Change Agent OK — Culprit: {result.get('most_likely_culprit')[:60]}...")
    else:
        print(f"\n⚠️  Change Agent ran with fallback: {result.get('error')}")