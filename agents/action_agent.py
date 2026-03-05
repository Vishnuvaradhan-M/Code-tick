# agents/action_agent.py
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.llm_client import call_llm
from dotenv import load_dotenv

load_dotenv()

PROMPT = """
You have a confirmed root cause. Give exact fix steps for the SRE team.

Root cause analysis: {hypothesis}
Service: {service_name}
Platform: Kubernetes

Return ONLY valid JSON with exactly these keys:
{{
    "recommended_action": "Rollback checkout-service to previous stable version",
    "action_type": "rollback",
    "steps": [
        "kubectl rollout undo deployment/checkout-service",
        "kubectl rollout status deployment/checkout-service",
        "Verify error rate drops below 1% in Prometheus dashboard",
        "Notify team in Slack #incidents channel that rollback is complete"
    ],
    "primary_command": "kubectl rollout undo deployment/checkout-service",
    "estimated_recovery_minutes": 4,
    "risk_level": "LOW",
    "risk_explanation": "Previous version was stable. Rollback is reversible and safe.",
    "verification_step": "Watch error rate in Prometheus drop below 1% within 4 minutes",
    "confidence": 94,
    "agent": "action_agent"
}}
"""


def run_action_agent(hypothesis: dict, service_name: str) -> dict:
    prompt = PROMPT.format(
        hypothesis=json.dumps(hypothesis, indent=2),
        service_name=service_name
    )
    try:
        text = call_llm(prompt)
        return _safe_parse(text, "action_agent")
    except Exception as e:
        return {
            "recommended_action": "Rollback checkout-service to previous stable version",
            "steps": [
                "kubectl rollout undo deployment/checkout-service",
                "kubectl rollout status deployment/checkout-service",
                "Verify error rate drops below 1%",
                "Notify team in Slack #incidents channel"
            ],
            "primary_command": "kubectl rollout undo deployment/checkout-service",
            "estimated_recovery_minutes": 4,
            "risk_level": "LOW",
            "confidence": 90,
            "error": str(e),
            "agent": "action_agent"
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
        "recommended_action": "Rollback checkout-service to previous stable version",
        "steps": [
            "kubectl rollout undo deployment/checkout-service",
            "Verify error rate drops below 1%"
        ],
        "primary_command": "kubectl rollout undo deployment/checkout-service",
        "estimated_recovery_minutes": 4,
        "risk_level": "LOW",
        "confidence": 80,
        "error": "parse_failed",
        "agent": agent
    }


if __name__ == "__main__":
    hypothesis = {
        "final_verdict": "Memory exhaustion from DB connection pool misconfiguration in commit abc123x",
        "confidence": 91,
        "supporting_commit": "abc123x"
    }

    print("Testing Action Agent...")
    print("-" * 40)
    result = run_action_agent(hypothesis, "checkout-service")
    print(json.dumps(result, indent=2))

    if "steps" in result and "error" not in result:
        print(f"\n✅ Action Agent OK — Action: {result.get('recommended_action')}")
    else:
        print(f"\n⚠️  Action Agent ran with fallback")