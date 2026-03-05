# scripts/test_websocket.py
import asyncio
import httpx
import json
import websockets


BACKEND_URL = "http://localhost:8000"
WS_URL      = "ws://localhost:8000/ws/incident"


async def test():
    print(f"Connecting to WebSocket at {WS_URL} ...")

    async with websockets.connect(WS_URL) as ws:
        print("Connected. Triggering incident via HTTP...")

        # Small delay to ensure WS handler is ready and waiting
        await asyncio.sleep(0.5)

        async with httpx.AsyncClient() as client:
            r = await client.post(f"{BACKEND_URL}/trigger-incident")
            print(f"Trigger response: {r.json()}")

        print("Waiting for agent updates...")

        while True:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=120.0)
                msg = json.loads(raw)

                event = msg.get("event", "")

                if event == "agent_update":
                    agent  = msg.get("agent", "")
                    status = msg.get("status", "").upper()
                    finding = msg.get("finding", "")
                    conf   = msg.get("confidence", 0)
                    print(f"  [{agent}] {status} — {finding} ({conf}%)")

                elif event == "complete":
                    print("\n════ PIPELINE COMPLETE ════")
                    print(f"Root Cause  : {msg.get('root_cause')}")
                    print(f"Confidence  : {msg.get('confidence')}%")
                    print(f"Fix         : {msg.get('recommended_action')}")
                    print(f"Command     : {msg.get('primary_command')}")
                    print(f"Risk        : {msg.get('risk_level')}")
                    print(f"Recovery    : {msg.get('estimated_recovery_minutes')} min")
                    print(f"Commit      : {msg.get('supporting_commit')}")
                    break

                elif event == "error":
                    print(f"\n❌ Error: {msg.get('message')}")
                    break

            except asyncio.TimeoutError:
                print("⚠️  Timeout — no response in 120 seconds")
                break


if __name__ == "__main__":
    asyncio.run(test())