# agents/orchestrator.py
import asyncio, json, os, sys
from typing import TypedDict, Optional
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, END
from agents.signal_agent import run_signal_agent
from agents.change_agent import run_change_agent
from agents.hypothesis_agent import run_hypothesis_agent
from agents.action_agent import run_action_agent
from data.test_incident import MOCK_METRICS, MOCK_COMMITS, MOCK_PAST_INCIDENTS, INCIDENT_META

class IncidentState(TypedDict):
    metrics_data: dict
    commit_history: list
    past_incidents: list
    incident_time: str
    service_name: str
    signal_findings: Optional[dict]
    change_findings: Optional[dict]
    hypothesis_findings: Optional[dict]
    action_findings: Optional[dict]
    current_step: str

ws_callback = None

def set_ws_callback(callback):
    global ws_callback
    ws_callback = callback

async def notify(agent, status, finding="", confidence=0):
    if ws_callback:
        await ws_callback({"event": "agent_update", "agent": agent, "status": status, "finding": finding, "confidence": confidence})

async def signal_node(state):
    await notify("signal_agent", "working")
    print("  [Signal Agent] Analyzing metrics...")
    result = await run_signal_agent(state["metrics_data"], state["past_incidents"], state["incident_time"])
    finding = result.get("anomalies_found", [""])[0] if result.get("anomalies_found") else ""
    await notify("signal_agent", "complete", finding=finding, confidence=result.get("confidence", 0))
    print(f"  [Signal Agent] Done — {result.get('severity', 'unknown')}")
    return {**state, "signal_findings": result, "current_step": "signal_done"}

async def change_node(state):
    await notify("change_agent", "working")
    print("  [Change Agent] Scanning commits...")
    result = await run_change_agent(state["commit_history"], state.get("signal_findings", {}), state["incident_time"])
    culprit = result.get("most_likely_culprit", {})
    await notify("change_agent", "complete", finding=culprit.get("reason", ""), confidence=result.get("confidence", 0))
    print(f"  [Change Agent] Done — culprit: {culprit.get('sha', 'none')}")
    return {**state, "change_findings": result, "current_step": "change_done"}

async def hypothesis_node(state):
    await notify("hypothesis_agent", "working")
    print("  [Hypothesis Agent] Synthesizing findings...")
    result = await run_hypothesis_agent(state.get("signal_findings", {}), state.get("change_findings", {}), state["incident_time"], state["service_name"])
    verdict = result.get("final_verdict", {})
    await notify("hypothesis_agent", "complete", finding=verdict.get("root_cause", ""), confidence=verdict.get("confidence", 0))
    print(f"  [Hypothesis Agent] Done — confidence: {verdict.get('confidence')}%")
    return {**state, "hypothesis_findings": result, "current_step": "hypothesis_done"}

async def action_node(state):
    await notify("action_agent", "working")
    print("  [Action Agent] Generating fix...")
    result = await run_action_agent(state.get("hypothesis_findings", {}), state["service_name"])
    await notify("action_agent", "complete", finding=result.get("recommended_action", ""), confidence=100)
    print(f"  [Action Agent] Done — {result.get('recommended_action', 'unknown')}")
    return {**state, "action_findings": result, "current_step": "complete"}

def build_graph():
    graph = StateGraph(IncidentState)
    graph.add_node("signal", signal_node)
    graph.add_node("change", change_node)
    graph.add_node("hypothesis", hypothesis_node)
    graph.add_node("action", action_node)
    graph.set_entry_point("signal")
    graph.add_edge("signal", "change")
    graph.add_edge("change", "hypothesis")
    graph.add_edge("hypothesis", "action")
    graph.add_edge("action", END)
    return graph.compile()

async def run_incident_swarm(metrics_data=None, commit_history=None, past_incidents=None, incident_time=None, service_name="checkout-service"):
    state = IncidentState(
        metrics_data=metrics_data or MOCK_METRICS,
        commit_history=commit_history or MOCK_COMMITS,
        past_incidents=past_incidents or MOCK_PAST_INCIDENTS,
        incident_time=incident_time or INCIDENT_META["alert_time"],
        service_name=service_name,
        signal_findings=None, change_findings=None,
        hypothesis_findings=None, action_findings=None,
        current_step="starting"
    )
    graph = build_graph()
    print("\n🚨 INCIDENT SWARM ACTIVATED")
    print("-" * 40)
    final_state = await graph.ainvoke(state)
    print("-" * 40)
    print("✅ ALL AGENTS COMPLETE")
    return final_state

if __name__ == "__main__":
    async def test():
        result = await run_incident_swarm()
        verdict = result.get("hypothesis_findings", {}).get("final_verdict", {})
        action = result.get("action_findings", {})
        print(f"\n════ FINAL RESULT ════")
        print(f"Root Cause:  {verdict.get('root_cause')}")
        print(f"Confidence:  {verdict.get('confidence')}%")
        print(f"Fix:         {action.get('recommended_action')}")
        print(f"Recovery:    {action.get('estimated_recovery_minutes')} minutes")
    asyncio.run(test())