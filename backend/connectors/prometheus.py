# backend/connectors/prometheus.py
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

GITEA_URL   = os.getenv("GITEA_URL",       "https://gitea-production-9a70.up.railway.app")
GITEA_TOKEN = os.getenv("GITEA_API_TOKEN", "69f74842ce36757550ae567cf57c30d66fa8155e")


async def fetch_real_metrics() -> dict:
    """Read real metrics from Gitea's built-in /metrics endpoint."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{GITEA_URL}/metrics",
                headers={"Authorization": f"token {GITEA_TOKEN}"}
            )
        if r.status_code != 200:
            print(f"Metrics endpoint {r.status_code} — using mock")
            return _fallback()
        return _parse(r.text)
    except Exception as e:
        print(f"Metrics fetch error: {e} — using mock")
        return _fallback()


def _parse(text: str) -> dict:
    values = {}
    for line in text.split("\n"):
        if line.startswith("#") or not line.strip():
            continue
        try:
            key = line.split(" ")[0].split("{")[0]
            val = float(line.split(" ")[-1])
            values[key] = val
        except Exception:
            continue

    http_req   = values.get("gitea_http_requests_total", 100)
    http_err   = values.get("gitea_http_request_errors_total", 2)
    error_rate = round((http_err / http_req) * 100, 2) if http_req > 0 else 0.0

    return {
        "service":            "checkout-service",
        "timestamp":          "live",
        "cpu_percent":        min(values.get("process_cpu_seconds_total", 15) * 8, 99),
        "memory_percent":     round(
            values.get("process_resident_memory_bytes", 200_000_000) / 5_000_000, 1
        ),
        "error_rate_percent": error_rate,
        "response_time_ms":   values.get(
            "gitea_http_request_duration_seconds_sum", 0.12
        ) * 1000,
        "normal_cpu":         20,
        "normal_memory":      40,
        "normal_error_rate":  1.0,
    }


def _fallback() -> dict:
    from data.test_incident import MOCK_METRICS
    return MOCK_METRICS