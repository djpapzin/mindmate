import os
import requests

api_key = os.environ.get('RENDER_API_KEY')
if not api_key:
    print('NO_KEY')
    raise SystemExit(1)

headers = {
    'Authorization': f'Bearer {api_key}'
}
url = 'https://api.render.com/v1/services/srv-d62nnqkr85hc739oc0kg/env-vars'
resp = requests.get(url, headers=headers)
print(resp.status_code)
print(resp.text)
