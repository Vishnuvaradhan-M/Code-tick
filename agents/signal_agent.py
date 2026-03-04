# agents/signal_agent.py
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.llm_client import call_llm
from dotenv import load_dotenv
load_dotenv()

PROMPT = """
Analyze these production metrics and identify the incident.
Incident time: {incident_time}
Metrics: {metrics_data}
Past incidents: {past_incidents}

Return ONLY valid JSON:
{{
    "affected_service": "checkout-service",
    "anomalies_found": ["CPU spiked to 94%", "Memory at 91%", "Error rate 22%"],
    "severity": "P1",
    "severity_reason": "Multiple critical metrics breached simultaneously",
    "key_signals": ["CPU and memory spike at same timestamp"],
    "spike_started_at": "2025-03-07T02:14:00Z",
    "normal_vs_current": {{
        "response_time": "was 120ms now 4200ms",
        "error_rate": "was 0.1% now 22.4%",
        "memory": "was 40% now 91.7%"
    }},
    "confidence": 91,
    "agent": "signal_agent"
}}
"""

async def run_signal_agent(metrics_data, past_incidents, incident_time):
    prompt = PROMPT.format(
        incident_time=incident_time,
        metrics_data=json.dumps(metrics_data, indent=2),
        past_incidents=json.dumps(past_incidents, indent=2)
    )
    try:
        text = call_llm(prompt)
        return safe_parse(text, "signal_agent")
    except Exception as e:
        return {"error": str(e), "agent": "signal_agent", "confidence": 0}

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
    return {"error": "parse_failed", "raw": text[:200], "agent": agent, "confidence": 0}

if __name__ == "__main__":
    import asyncio
    from data.test_incident import MOCK_METRICS, MOCK_PAST_INCIDENTS, INCIDENT_META
    print("Testing Signal Agent...")
    print("-" * 40)
    result = asyncio.run(run_signal_agent(MOCK_METRICS, MOCK_PAST_INCIDENTS, INCIDENT_META["alert_time"]))
    print(json.dumps(result, indent=2))
    if "error" not in result:
        print(f"\n✅ Signal Agent working — Severity: {result.get('severity')} — Confidence: {result.get('confidence')}%")
    else:
        print(f"\n❌ Failed: {result.get('error')}")