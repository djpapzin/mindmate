import os
import requests

STAGING_SERVICE_ID = "srv-d61nle4oud1c73aggvf0"
ENV_VAR_KEY = "ENV"
ENV_VAR_VALUE = "staging"

api_key = os.environ.get("RENDER_API_KEY")

if not api_key:
    raise SystemExit("Missing RENDER_API_KEY")

url = f"https://api.render.com/v1/services/{STAGING_SERVICE_ID}/env-vars/{ENV_VAR_KEY}"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
payload = {
    "value": ENV_VAR_VALUE
}

resp = requests.put(url, headers=headers, json=payload)
print(f"Status Code: {resp.status_code}")
print(f"Response: {resp.text}")
