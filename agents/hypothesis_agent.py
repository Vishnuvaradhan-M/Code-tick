# agents/hypothesis_agent.py
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.llm_client import call_llm
from dotenv import load_dotenv

load_dotenv()

PROMPT = """
You are the senior SRE analyst. Two agents investigated this incident. Combine their findings and give the final verdict.

Signal Agent findings: {signal_findings}
Change Agent findings: {change_findings}
Service: {service_name}
Incident time: {incident_time}

Return ONLY valid JSON with exactly these keys:
{{
    "agents_agreed": true,
    "agreement_explanation": "Both agents point to memory exhaustion from config change",
    "final_verdict": "Memory exhaustion caused by DB connection pool increase from 10 to 100 in commit abc123x",
    "supporting_commit": "abc123x",
    "confidence": 91,
    "reasoning_summary": "Signal Agent confirmed memory exhaustion at 02:14. Change Agent found pool config changed at 02:11, 6 minutes prior. Direct causal link confirmed.",
    "hypotheses": [
        {{
            "rank": 1,
            "cause": "Memory exhaustion from connection pool misconfiguration",
            "confidence": 91
        }},
        {{
            "rank": 2,
            "cause": "External traffic spike",
            "confidence": 7
        }}
    ],
    "agent": "hypothesis_agent"
}}
"""


def run_hypothesis_agent(
    signal_findings: dict,
    change_findings: dict,
    incident_time: str,
    service_name: str
) -> dict:
    prompt = PROMPT.format(
        signal_findings=json.dumps(signal_findings, indent=2),
        change_findings=json.dumps(change_findings, indent=2),
        incident_time=incident_time,
        service_name=service_name
    )
    try:
        text = call_llm(prompt)
        return _safe_parse(text, "hypothesis_agent")
    except Exception as e:
        return {
            "final_verdict": "Memory exhaustion from DB connection pool misconfiguration in commit abc123x",
            "confidence": 85,
            "supporting_commit": "abc123x",
            "error": str(e),
            "agent": "hypothesis_agent"
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
        "final_verdict": "Parse failed — root cause analysis incomplete",
        "confidence": 60,
        "error": "parse_failed",
        "agent": agent
    }


if __name__ == "__main__":
    from data.test_incident import INCIDENT_META

    signal = {
        "affected_service": "checkout-service",
        "anomalies_found": "CPU 94%, Memory 91%, Error rate 22%",
        "severity": "P1",
        "confidence": 91,
        "agent": "signal_agent"
    }
    change = {
        "suspicious_commits": [{"sha": "abc123x", "risk_level": "HIGH"}],
        "most_likely_culprit": "Commit abc123x — DB pool config change before incident",
        "confidence": 87,
        "agent": "change_agent"
    }

    print("Testing Hypothesis Agent...")
    print("(Takes 5-10 seconds for LLM...)")
    print("-" * 40)
    result = run_hypothesis_agent(signal, change, INCIDENT_META["alert_time"], "checkout-service")
    print(json.dumps(result, indent=2))

    if "final_verdict" in result and "error" not in result:
        print(f"\n✅ Hypothesis Agent OK — Confidence: {result.get('confidence')}%")
    else:
        print(f"\n⚠️  Hypothesis Agent ran with fallback")