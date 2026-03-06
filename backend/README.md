# Initial Backend Implementation Documentation

## Project Structure
The backend is organized as follows:
- `app/main.py`: Application entry point.
- `app/models/`: Database models (SQLAlchemy).
- `app/schemas/`: Data validation (Pydantic).
- `app/routes/`: API & WebSocket endpoints.
- `app/services/`: Business logic (SOS, Pulse, Telemetry).
- `app/core/`: Central managers (WebSockets).

## Setup Instructions
1. Install dependencies: `pip install -r requirements.txt`
2. Configure `.env` based on `.env.example`.
3. Run with uvicorn: `uvicorn app.main:app --reload`
4. Or use Docker: `docker-compose up --build`

## Real-Time updates
- Use WebSocket at `/ws/sos` for global alerts.
- Use WebSocket at `/ws/telemetry/{device_id}` for specific device tracking.
