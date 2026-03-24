from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    PROJECT_NAME: str = "Life Link SOS Backend"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    DEVICE_API_KEY: str = "change-me-device-key"

    SECRET_KEY: str = "change-me-secret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Optional secure ingest support for /telemetry/secure
    AES_KEY: str = ""
    AES_IV: str = ""

    CORS_ORIGINS: str = "*"


settings = Settings()