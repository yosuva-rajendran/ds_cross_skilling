from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    qdrant_host: str
    qdrant_port:str
    google_api_key:str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()