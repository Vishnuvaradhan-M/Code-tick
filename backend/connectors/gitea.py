# backend/connectors/gitea.py
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

GITEA_URL   = os.getenv("GITEA_URL",          "https://gitea-production-9a70.up.railway.app")
GITEA_TOKEN = os.getenv("GITEA_API_TOKEN",    "69f74842ce36757550ae567cf57c30d66fa8155e")
REPO_OWNER  = os.getenv("GITEA_REPO_OWNER",   "incidentadmin")
REPO_NAME   = os.getenv("GITEA_REPO_NAME",    "checkout-service")


async def fetch_recent_commits(limit: int = 10) -> list:
    url    = f"{GITEA_URL}/api/v1/repos/{REPO_OWNER}/{REPO_NAME}/commits"
    params = {"limit": limit, "token": GITEA_TOKEN}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, params=params)
        if r.status_code != 200:
            print(f"Gitea API {r.status_code} — using mock data")
            from data.test_incident import MOCK_COMMITS
            return MOCK_COMMITS
        return [
            {
                "sha":           c["sha"][:7],
                "message":       c["commit"]["message"],
                "author":        c["commit"]["author"]["name"],
                "timestamp":     c["commit"]["author"]["date"],
                "files_changed": ["config"],
            }
            for c in r.json()
        ]
    except Exception as e:
        print(f"Gitea fetch error: {e} — using mock data")
        from data.test_incident import MOCK_COMMITS
        return MOCK_COMMITS