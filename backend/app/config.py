from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./app.db"
    secret_key: str = "change-me"
    cookie_encryption_key: str = ""
    browser_use_api_key: str = ""
    anthropic_api_key: str = ""
    fal_api_key: str = ""
    cors_origins: str = "http://localhost:3000"
    access_token_expire_minutes: int = 1440  # 24 hours

    model_config = {"env_file": ".env"}


settings = Settings()
