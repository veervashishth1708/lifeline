import requests
import json

url = "http://localhost:8000/api/v1/telemetry"
headers = {
    "Content-Type": "application/json",
    "X-Device-Key": "antigravity_secret_123"
}
payload = {
    "device_id": "midway_panel",
    "latitude": 30.686199,
    "longitude": 76.661903,
    "pulse": 72,
    "sos": True,
    "is_checkpoint": False,
    "user_id": ""
}

try:
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
