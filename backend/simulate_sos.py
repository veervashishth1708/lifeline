import httpx
import json
import asyncio

async def simulate_sos():
    url = "http://127.0.0.1:8000/api/v1/telemetry"
    headers = {
        "x-device-key": "antigravity_secret_123",
        "Content-Type": "application/json"
    }
    payload = {
        "device_id": "node_b_sim",
        "latitude": 30.6830,
        "longitude": 76.6058,
        "pulse": 110,
        "sos": True,
        "timestamp": None,
        "is_checkpoint": False,
        "user_id": None
    }
    
    print(f"Sending SOS payload to {url}...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(simulate_sos())
