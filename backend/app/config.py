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

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
