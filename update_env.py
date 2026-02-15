import os
import json
import requests

SERVICE_ID = "srv-d62nnqkr85hc739oc0kg"
NEW_REDIS_URL = "redis://red-d68oj2bh46gs73fi3j6g.oregon-redis.render.com:6379"
api_key = os.environ.get("RENDER_API_KEY")

if not api_key:
    raise SystemExit("Missing RENDER_API_KEY")

url = f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
payload = {
    "envVars": [
        {"key": "REDIS_URL", "value": NEW_REDIS_URL}
    ]
}

resp = requests.put(url, headers=headers, data=json.dumps(payload))
print(resp.status_code)
print(resp.text)
