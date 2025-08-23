from pydantic_settings import SettingsConfigDict, BaseSettings


class Settings(BaseSettings):
    GATEWAY_SERVICE_NAME: str = "FastAPI Gateway"
    GATEWAY_SERVICE_VERSION: str = "0.1.0"
    GATEWAY_DATABASE_URL: str = "sqlite:///./database.db"
    GATEWAY_RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    GATEWAY_SERVICE_PORT: int = 8000
    GATEWAY_USERS_SERVICE_URL: str = "http://users:8000"
    GATEWAY_ENVIRONMENT: str = "development"
    GATEWAY_SENTRY_DSN: str = ""
    GATEWAY_SENTRY_RELEASE: str = "0.1.0"

    GATEWAY_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    GATEWAY_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    GATEWAY_PRIVATE_KEY: str = "./certs/private.pem"
    GATEWAY_PUBLIC_KEY: str = "./certs/public.pem"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
