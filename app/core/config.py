from pydantic_settings import SettingsConfigDict, BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "FastAPI Gateway"
    SERVICE_VERSION: str = "0.1.0"
    DATABASE_URL: str = "sqlite:///./database.db"
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    SERVICE_PORT: int = 8000
    USERS_SERVICE_URL: str = "http://users:8000"
    ENVIRONMENT: str = "development"
    SENTRY_DSN: str = ""
    SENTRY_RELEASE: str = "0.1.0"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="GATEWAY_"  # Prefisso di tutte le variabili (es. GATEWAY_DATABASE_URL)
    )


settings = Settings()
