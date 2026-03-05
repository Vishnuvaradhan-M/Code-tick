# agents/orchestrator.py
import asyncio
from typing import TypedDict, Optional, Callable

from langgraph.graph import StateGraph, END

from agents.signal_agent     import run_signal_agent
from agents.change_agent     import run_change_agent
from agents.hypothesis_agent import run_hypothesis_agent
from agents.action_agent     import run_action_agent


# ── WebSocket callback ───────────────────────────────────────────────────────
_ws_callback: Optional[Callable] = None


def set_ws_callback(callback: Callable):
    global _ws_callback
    _ws_callback = callback


async def _broadcast(message: dict):
    if _ws_callback:
        await _ws_callback(message)


# ── Shared State ─────────────────────────────────────────────────────────────
class IncidentState(TypedDict):
    service_name:        str
    incident_time:       str
    metrics_data:        dict
    commit_history:      list
    past_incidents:      list
    signal_findings:     dict
    change_findings:     dict
    hypothesis_findings: dict
    action_findings:     dict


# ── Agent Nodes (async nodes, sync agent calls) ───────────────────────────────
async def signal_node(state: IncidentState) -> IncidentState:
    await _broadcast({
        "event": "agent_update", "agent": "signal_agent",
        "status": "working",
        "finding": "Scanning Prometheus metrics...",
        "confidence": 0
    })

    # ✅ NO await — run_signal_agent is sync
    result = run_signal_agent(
        state["metrics_data"],
        state["past_incidents"],
        state["incident_time"]
    )

    await _broadcast({
        "event": "agent_update", "agent": "signal_agent",
        "status": "complete",
        "finding": str(result.get("anomalies_found", "Anomalies detected")),
        "confidence": result.get("confidence", 85)
    })
    return {**state, "signal_findings": result}


async def change_node(state: IncidentState) -> IncidentState:
    await _broadcast({
        "event": "agent_update", "agent": "change_agent",
        "status": "working",
        "finding": "Reading Gitea commit history...",
        "confidence": 0
    })

    # ✅ NO await — run_change_agent is sync
    result = run_change_agent(
        state["commit_history"],
        state["signal_findings"],
        state["incident_time"]
    )

    await _broadcast({
        "event": "agent_update", "agent": "change_agent",
        "status": "complete",
        "finding": str(result.get("most_likely_culprit", "Culprit identified")),
        "confidence": result.get("confidence", 80)
    })
    return {**state, "change_findings": result}


async def hypothesis_node(state: IncidentState) -> IncidentState:
    await _broadcast({
        "event": "agent_update", "agent": "hypothesis_agent",
        "status": "working",
        "finding": "Synthesizing signal + change findings...",
        "confidence": 0
    })

    # ✅ NO await — run_hypothesis_agent is sync
    result = run_hypothesis_agent(
        state["signal_findings"],
        state["change_findings"],
        state["incident_time"],
        state["service_name"]
    )

    await _broadcast({
        "event": "agent_update", "agent": "hypothesis_agent",
        "status": "complete",
        "finding": str(result.get("final_verdict", "Root cause identified")),
        "confidence": result.get("confidence", 88)
    })
    return {**state, "hypothesis_findings": result}


async def action_node(state: IncidentState) -> IncidentState:
    await _broadcast({
        "event": "agent_update", "agent": "action_agent",
        "status": "working",
        "finding": "Generating fix steps...",
        "confidence": 0
    })

    # ✅ NO await — run_action_agent is sync
    result = run_action_agent(
        state["hypothesis_findings"],
        state["service_name"]
    )

    await _broadcast({
        "event": "agent_update", "agent": "action_agent",
        "status": "complete",
        "finding": str(result.get("recommended_action", "Fix steps ready")),
        "confidence": result.get("confidence", 90)
    })
    return {**state, "action_findings": result}


# ── Graph ─────────────────────────────────────────────────────────────────────
def _build_graph():
    g = StateGraph(IncidentState)
    g.add_node("signal",     signal_node)
    g.add_node("change",     change_node)
    g.add_node("hypothesis", hypothesis_node)
    g.add_node("action",     action_node)
    g.set_entry_point("signal")
    g.add_edge("signal",     "change")
    g.add_edge("change",     "hypothesis")
    g.add_edge("hypothesis", "action")
    g.add_edge("action",     END)
    return g.compile()


# ── Public Entry Point ────────────────────────────────────────────────────────
async def run_incident_swarm(
    metrics_data:   dict = None,
    commit_history: list = None
) -> dict:

    from data.test_incident import (
        MOCK_METRICS, MOCK_COMMITS,
        MOCK_PAST_INCIDENTS, INCIDENT_META
    )

    metrics = metrics_data   or MOCK_METRICS
    commits = commit_history or MOCK_COMMITS

    initial = IncidentState(
        service_name        = INCIDENT_META["service_name"],
        incident_time       = INCIDENT_META["alert_time"],
        metrics_data        = metrics,
        commit_history      = commits,
        past_incidents      = MOCK_PAST_INCIDENTS,
        signal_findings     = {},
        change_findings     = {},
        hypothesis_findings = {},
        action_findings     = {},
    )

    graph       = _build_graph()
    final_state = await graph.ainvoke(initial)

    h = final_state["hypothesis_findings"]
    a = final_state["action_findings"]

    return {
        "root_cause":                 h.get("final_verdict", "Unknown"),
        "recommended_action":         a.get("recommended_action", "Manual investigation"),
        "steps":                      a.get("steps", []),
        "primary_command":            a.get("primary_command", ""),
        "confidence":                 h.get("confidence", 0),
        "risk_level":                 a.get("risk_level", "MEDIUM"),
        "estimated_recovery_minutes": a.get("estimated_recovery_minutes", 10),
        "supporting_commit":          final_state["change_findings"].get(
                                          "most_likely_culprit", ""
                                      ),
    }


# ── Local Test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    async def test():
        print("Running full pipeline test...\n")
        result = await run_incident_swarm()
        print("\n════ FINAL RESULT ════")
        print(f"Root Cause : {result['root_cause']}")
        print(f"Confidence : {result['confidence']}%")
        print(f"Fix        : {result['recommended_action']}")
        print(f"Recovery   : {result['estimated_recovery_minutes']} min")
        print(f"Command    : {result['primary_command']}")
        print(f"Risk       : {result['risk_level']}")
        print("═" * 40)

    asyncio.run(test())