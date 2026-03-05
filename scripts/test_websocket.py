# scripts/test_websocket.py
import asyncio
import websockets
import httpx
import json


async def test():
    print("Connecting to WebSocket at ws://localhost:8000/ws/incident ...")

    async with websockets.connect("ws://localhost:8000/ws/incident") as ws:
        print("Connected. Triggering incident via HTTP...")

        async with httpx.AsyncClient() as client:
            resp = await client.post("http://localhost:8000/trigger-incident")
            print(f"Trigger response: {resp.json()}")

        print("Waiting for agent updates...\n")

        while True:
            raw  = await ws.recv()
            data = json.loads(raw)
            event = data.get("event")

            if event == "agent_update":
                agent      = data.get("agent", "")
                status     = data.get("status", "")
                finding    = data.get("finding", "")
                confidence = data.get("confidence", 0)
                print(f"  [{agent}] {status.upper()} — {finding} ({confidence}%)")

            elif event == "incident_complete":
                r = data.get("result", {})
                print("\n════ PIPELINE COMPLETE ════")
                print(f"Root Cause  : {r.get('root_cause')}")
                print(f"Confidence  : {r.get('confidence')}%")
                print(f"Fix         : {r.get('recommended_action')}")
                print(f"Command     : {r.get('primary_command')}")
                print(f"Risk        : {r.get('risk_level')}")
                print(f"Recovery    : {r.get('estimated_recovery_minutes')} min")
                break

            elif event == "error":
                print(f"ERROR: {data.get('message')}")
                break


asyncio.run(test())