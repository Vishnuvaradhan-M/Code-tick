import httpx, os
from dotenv import load_dotenv

load_dotenv()

base = os.getenv("GITEA_URL")
owner = os.getenv("GITEA_REPO_OWNER")
repo = os.getenv("GITEA_REPO_NAME")
token = os.getenv("GITEA_API_TOKEN")

url = f"{base}/api/v1/repos/{owner}/{repo}/commits"

print("Requesting:", url)

headers = {"Authorization": f"token {token}"}

r = httpx.get(url, headers=headers)

print("Status:", r.status_code)

commits = r.json()
for c in commits[:4]:
    print("-", c["sha"][:7], c["commit"]["message"])