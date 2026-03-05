# agents/signal_agent.py
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.llm_client import call_llm
from dotenv import load_dotenv

load_dotenv()

PROMPT = """
Analyze these production metrics and identify the incident.

Incident time: {incident_time}
Metrics: {metrics_data}
Past incidents: {past_incidents}

Return ONLY valid JSON with exactly these keys:
{{
    "affected_service": "checkout-service",
    "anomalies_found": "CPU spiked to 94%, Memory at 91%, Error rate 22%",
    "severity": "P1",
    "severity_reason": "Multiple critical metrics breached simultaneously",
    "key_signals": ["CPU and memory spike at same timestamp", "Error rate 22x normal"],
    "spike_started_at": "2026-03-07T02:14:00Z",
    "normal_vs_current": {{
        "response_time": "was 120ms now 3200ms",
        "error_rate": "was 1% now 22%",
        "memory": "was 40% now 91%"
    }},
    "confidence": 91,
    "agent": "signal_agent"
}}
"""


def run_signal_agent(metrics_data: dict, past_incidents: list, incident_time: str) -> dict:
    prompt = PROMPT.format(
        incident_time=incident_time,
        metrics_data=json.dumps(metrics_data, indent=2),
        past_incidents=json.dumps(past_incidents, indent=2)
    )
    try:
        text = call_llm(prompt)
        return _safe_parse(text, "signal_agent")
    except Exception as e:
        return {
            "anomalies_found": "Metrics analysis failed — using fallback",
            "severity": "P1",
            "confidence": 75,
            "error": str(e),
            "agent": "signal_agent"
        }


def _safe_parse(text: str, agent: str) -> dict:
    # Remove markdown code blocks if present
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])

    try:
        return json.loads(text)
    except Exception:
        # Try to find JSON object in response
        s = text.find("{")
        e = text.rfind("}") + 1
        if s != -1 and e > s:
            try:
                return json.loads(text[s:e])
            except Exception:
                pass

    return {
        "anomalies_found": "Parse failed — raw LLM response received",
        "severity": "P1",
        "confidence": 60,
        "error": "parse_failed",
        "raw": text[:200],
        "agent": agent
    }


if __name__ == "__main__":
    from data.test_incident import MOCK_METRICS, MOCK_PAST_INCIDENTS, INCIDENT_META

    print("Testing Signal Agent...")
    print("-" * 40)
    result = run_signal_agent(MOCK_METRICS, MOCK_PAST_INCIDENTS, INCIDENT_META["alert_time"])
    print(json.dumps(result, indent=2))

    if "error" not in result:
        print(f"\n✅ Signal Agent OK — Severity: {result.get('severity')} — Confidence: {result.get('confidence')}%")
    else:
        print(f"\n⚠️  Signal Agent ran with fallback: {result.get('error')}")