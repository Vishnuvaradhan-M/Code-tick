# agents/action_agent.py
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.llm_client import call_llm
from dotenv import load_dotenv
load_dotenv()

PROMPT = """
You have a confirmed root cause. Give exact fix steps.
Root cause: {hypothesis}
Service: {service_name}
Platform: Kubernetes on AWS

Return ONLY valid JSON:
{{
    "recommended_action": "Rollback checkout-service to v2.3.0",
    "action_type": "rollback",
    "steps": [
        "kubectl rollout undo deployment/checkout-service",
        "kubectl get pods -n production (watch pods restart)",
        "Confirm error rate drops below 1% in metrics",
        "Notify team in Slack #incidents channel"
    ],
    "primary_command": "kubectl rollout undo deployment/checkout-service",
    "estimated_recovery_minutes": 4,
    "risk_level": "LOW",
    "risk_explanation": "Previous version was stable for 3 weeks before this change",
    "rollback_commit": "def456",
    "verification_step": "Watch error rate in Prometheus drop below 1%",
    "agent": "action_agent"
}}
"""

async def run_action_agent(hypothesis, service_name):
    prompt = PROMPT.format(
        hypothesis=json.dumps(hypothesis, indent=2),
        service_name=service_name
    )
    try:
        text = call_llm(prompt)
        return safe_parse(text, "action_agent")
    except Exception as e:
        return {"error": str(e), "agent": "action_agent"}

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
    return {"error": "parse_failed", "agent": agent}

if __name__ == "__main__":
    import asyncio
    hypothesis = {"final_verdict": {"root_cause": "Memory exhaustion from connection pool misconfiguration in commit abc123", "supporting_commit": "abc123", "confidence": 91}}
    print("Testing Action Agent...")
    print("-" * 40)
    result = asyncio.run(run_action_agent(hypothesis, "checkout-service"))
    print(json.dumps(result, indent=2))
    if "steps" in result:
        print(f"\n✅ Action Agent working — Action: {result.get('recommended_action')}")
    else:
        print(f"\n❌ Check output")