from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>E2EE Decryption Monitor</title>
        <style>
            body { font-family: 'Courier New', Courier, monospace; background-color: #0f172a; color: #38bdf8; margin: 0; padding: 20px; }
            h1 { color: #f8fafc; text-align: center; }
            .container { max-width: 800px; margin: 0 auto; }
            .log-box { background: #1e293b; padding: 15px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border-left: 5px solid #0ea5e9; }
            .log-box.sos { border-left-color: #ef4444; color: #fca5a5; }
            .label { font-weight: bold; color: #94a3b8; margin-top: 10px; display: inline-block; }
            .value { margin-left: 10px; word-break: break-all; }
            .key { color: #84cc16; }
            .status { text-align: center; color: #22c55e; margin-bottom: 20px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>E2EE Decryption Monitor</h1>
            <div class="status" id="status">Listening for payloads on Port 8001...</div>
            <div id="logs"></div>
        </div>
        <script>
            var ws = new WebSocket("ws://localhost:8001/ws");
            ws.onmessage = function(event) {
                var data = JSON.parse(event.data);
                var logsDiv = document.getElementById('logs');
                var div = document.createElement('div');
                div.className = 'log-box' + (data.decrypted_data.includes('SOS') ? ' sos' : '');
                
                div.innerHTML = `
                    <div><span class="label">Time:</span> <span class="value">${new Date().toLocaleTimeString()}</span></div>
                    <div><span class="label">Receiver:</span> <span class="value">Midway Panel (Zero-Knowledge)</span></div>
                    <div><span class="label">AES Key:</span> <span class="value key">${data.aes_key}</span></div>
                    <div><span class="label">Encrypted Payload:</span> <span class="value">${data.encrypted_data}</span></div>
                    <hr style="border: 0; border-top: 1px solid #334155; margin: 15px 0;">
                    <div><span class="label">Decrypted Data:</span> <span class="value" style="color: #fafafa; font-size: 1.1em;">${data.decrypted_data}</span></div>
                `;
                
                logsDiv.insertBefore(div, logsDiv.firstChild);
            };
        </script>
    </body>
</html>
"""

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/decoder-update")
async def update_decoder(payload: dict):
    # This receives {"encrypted_data": "...", "decrypted_data": "...", "aes_key": "..."}
    await manager.broadcast(payload)
    return {"status": "ok"}
