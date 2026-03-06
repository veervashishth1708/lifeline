import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
DEVICE_KEY = "antigravity_secret_123"

def test_devices_status():
    print("Testing GET /devices/status...")
    response = requests.get(f"{BASE_URL}/devices/status")
    if response.status_code == 200:
        print("Success!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Failed with status code: {response.status_code}")
        print(response.text)

def simulate_telemetry():
    print("\nSimulating telemetry to register a device...")
    payload = {
        "device_id": "test_device_001",
        "latitude": 30.6830,
        "longitude": 76.6058,
        "pulse": 75,
        "sos": False
    }
    headers = {
        "X-Device-Key": DEVICE_KEY
    }
    response = requests.post(f"{BASE_URL}/telemetry", json=payload, headers=headers)
    if response.status_code == 200:
        print("Telemetry posted successfully!")
    else:
        print(f"Failed to post telemetry: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    simulate_telemetry()
    test_devices_status()
