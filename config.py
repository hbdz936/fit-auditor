from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fitauditor"
    api_token: str = "change-me-in-prod"
    allowed_origins: str = "http://localhost:8000"
    environment: str = "development"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()