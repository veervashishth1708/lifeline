from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Antigravity SOS Backend"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "secret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "antigravity"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/antigravity"
    
    REDIS_URL: str = "redis://localhost:6379/0"
    
    N8N_WEBHOOK_URL: str = "http://localhost:5678/webhook/sos-alert"
    DEVICE_API_KEY: str = "antigravity_secret_123"
    
    # AES-256-CBC Encryption Settings (Keys match ESP32 codes)
    AES_KEY: str = "2b7e151628aed2a6abf7158809cf4f3c2b7e151628aed2a6abf7158809cf4f3c"
    AES_IV: str = "000102030405060708090a0b0c0d0e0f"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
