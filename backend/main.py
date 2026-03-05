# backend/main.py
import asyncio
import json
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="IncidentSwarm API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── State ────────────────────────────────────────────────────────────────────
_connections: list[WebSocket] = []
_status = {"running": False, "result": None}


# ── Routes ───────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "service": "IncidentSwarm"}


@app.get("/incident-status")
async def incident_status():
    return _status


@app.post("/trigger-incident")
async def trigger():
    if _status["running"]:
        return {"status": "already_running"}
    asyncio.create_task(_run_pipeline())
    return {"status": "started"}


@app.websocket("/ws/incident")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    _connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()   # keep alive
    except WebSocketDisconnect:
        if websocket in _connections:
            _connections.remove(websocket)


# ── Broadcast ─────────────────────────────────────────────────────────────────
async def _broadcast(message: dict):
    dead = []
    for ws in _connections:
        try:
            await ws.send_text(json.dumps(message))
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in _connections:
            _connections.remove(ws)


# ── Pipeline ──────────────────────────────────────────────────────────────────
async def _run_pipeline():
    _status["running"] = True
    _status["result"]  = None

    from agents.orchestrator            import run_incident_swarm, set_ws_callback
    from backend.connectors.gitea       import fetch_recent_commits
    from backend.connectors.prometheus  import fetch_real_metrics

    set_ws_callback(_broadcast)

    try:
        metrics = await fetch_real_metrics()
        commits = await fetch_recent_commits()

        result = await run_incident_swarm(
            metrics_data=metrics,
            commit_history=commits,
        )
        _status["result"] = result
        await _broadcast({"event": "incident_complete", "result": result})

    except Exception as e:
        print(f"Pipeline error: {e}")
        await _broadcast({"event": "error", "message": str(e)})

    finally:
        _status["running"] = False


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)