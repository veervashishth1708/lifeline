from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine, Base
from .routes import telemetry_routes, websocket_routes, sos_routes, auth_routes

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

from fastapi import Request
import json

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    if request.method == "POST" and "telemetry" in request.url.path:
        body = await request.body()
        print(f"DEBUG: Telemetry Request Body: {body.decode()}")
    response = await call_next(request)
    return response

# Include Routers
app.include_router(auth_routes.router, prefix=settings.API_V1_STR, tags=["auth"])
app.include_router(telemetry_routes.router, prefix=settings.API_V1_STR, tags=["telemetry"])
app.include_router(sos_routes.router, prefix=settings.API_V1_STR, tags=["sos"])
app.include_router(websocket_routes.router, tags=["websocket"])

@app.get("/")
async def root():
    return {"message": "Antigravity SOS Backend is running"}
