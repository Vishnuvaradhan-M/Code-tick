# agents/hypothesis_agent.py
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.llm_client import call_llm
from dotenv import load_dotenv
load_dotenv()

PROMPT = """
You are the senior analyst. Two agents investigated this incident.
Combine their findings and give the final verdict.

Signal Agent findings: {signal_findings}
Change Agent findings: {change_findings}
Service: {service_name}
Incident time: {incident_time}

Return ONLY valid JSON:
{{
    "agents_agreed": true,
    "agreement_explanation": "Both agents point to memory exhaustion from config change",
    "hypotheses": [
        {{
            "rank": 1,
            "cause": "Memory exhaustion caused by connection pool misconfiguration in commit abc123",
            "confidence": 91,
            "evidence_from_signal": "Memory jumped from 40% to 91% at 02:14 AM",
            "evidence_from_change": "Connection pool config changed 3 minutes before incident",
            "reasoning": "Pool size increased 10x consuming all available memory under normal load"
        }},
        {{
            "rank": 2,
            "cause": "External traffic spike coinciding with deploy",
            "confidence": 7,
            "evidence_from_signal": "High request rate",
            "evidence_from_change": "No evidence",
            "reasoning": "Possible but no traffic anomaly detected before config change"
        }},
        {{
            "rank": 3,
            "cause": "Database server degradation",
            "confidence": 2,
            "evidence_from_signal": "Minimal",
            "evidence_from_change": "None",
            "reasoning": "No database alerts fired independently"
        }}
    ],
    "final_verdict": {{
        "root_cause": "Memory exhaustion from connection pool misconfiguration in commit abc123",
        "supporting_commit": "abc123",
        "confidence": 91,
        "reasoning_summary": "Signal Agent confirmed memory exhaustion. Change Agent found config change 3 minutes prior. Both findings directly connect."
    }},
    "agent": "hypothesis_agent"
}}
"""

async def run_hypothesis_agent(signal_findings, change_findings, incident_time, service_name):
    prompt = PROMPT.format(
        signal_findings=json.dumps(signal_findings, indent=2),
        change_findings=json.dumps(change_findings, indent=2),
        incident_time=incident_time,
        service_name=service_name
    )
    try:
        text = call_llm(prompt)
        return safe_parse(text, "hypothesis_agent")
    except Exception as e:
        return {"error": str(e), "agent": "hypothesis_agent", "confidence": 0}

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
    from data.test_incident import INCIDENT_META
    signal = {"affected_service": "checkout-service", "anomalies_found": ["CPU 94%", "Memory 91%"], "severity": "P1", "confidence": 91, "agent": "signal_agent"}
    change = {"suspicious_commits": [{"sha": "abc123", "message": "Increase connection pool", "risk_level": "HIGH"}], "most_likely_culprit": {"sha": "abc123", "reason": "Timing + config type"}, "confidence": 87, "agent": "change_agent"}
    print("Testing Hypothesis Agent...")
    print("Takes 5-8 seconds...")
    print("-" * 40)
    result = asyncio.run(run_hypothesis_agent(signal, change, INCIDENT_META["alert_time"], "checkout-service"))
    print(json.dumps(result, indent=2))
    if "final_verdict" in result:
        v = result["final_verdict"]
        print(f"\n✅ Hypothesis Agent working — Confidence: {v.get('confidence')}%")
    else:
        print(f"\n❌ Check output")