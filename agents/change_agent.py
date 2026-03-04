# agents/change_agent.py
import json, os, sys
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
1. Commits within 30 minutes before incident = highly suspicious
2. Config file changes = more suspicious than code changes
3. Database or memory config = highest risk

Return ONLY valid JSON:
{{
    "suspicious_commits": [
        {{
            "sha": "abc123",
            "message": "Increase database connection pool size from 10 to 100",
            "author": "john.dev@shopeasy.com",
            "timestamp": "2025-03-07T02:11:00Z",
            "risk_level": "HIGH",
            "risk_reason": "Config change 3 minutes before incident affecting memory",
            "files_changed": ["config/database.yml"]
        }}
    ],
    "timing_correlation": "Deploy at 02:11 AM, incident at 02:14 AM — 3 minute gap",
    "most_likely_culprit": {{
        "sha": "abc123",
        "reason": "Connection pool config change directly before memory exhaustion"
    }},
    "no_relevant_changes": false,
    "confidence": 87,
    "agent": "change_agent"
}}
"""

async def run_change_agent(commit_history, signal_findings, incident_time):
    prompt = PROMPT.format(
        incident_time=incident_time,
        commit_history=json.dumps(commit_history, indent=2),
        signal_findings=json.dumps(signal_findings, indent=2)
    )
    try:
        text = call_llm(prompt)
        return safe_parse(text, "change_agent")
    except Exception as e:
        return {"error": str(e), "agent": "change_agent", "confidence": 0}

def safe_parse(text, agent):
    try:
        return json.loads(text)
    except:
        s, e = text.find("{"), text.rfind("}") + 1
        if s != -1 and e > s:
            try:
                return json.loads(text[s:e])
            except:
                pass
    return {"error": "parse_failed", "agent": agent, "confidence": 0}

if __name__ == "__main__":
    import asyncio
    from data.test_incident import MOCK_COMMITS, INCIDENT_META
    sample_signal = {"affected_service": "checkout-service", "severity": "P1", "confidence": 91}
    print("Testing Change Agent...")
    print("-" * 40)
    result = asyncio.run(run_change_agent(MOCK_COMMITS, sample_signal, INCIDENT_META["alert_time"]))
    print(json.dumps(result, indent=2))
    if "error" not in result:
        culprit = result.get("most_likely_culprit", {})
        print(f"\n✅ Change Agent working — Culprit: {culprit.get('sha')} — Confidence: {result.get('confidence')}%")
    else:
        print(f"\n❌ Failed: {result.get('error')}")