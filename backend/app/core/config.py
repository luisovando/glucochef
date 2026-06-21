from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
 
BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "GlucoChef Backend"
    debug: bool = False
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://glucochef:glucochef@localhost:5432/glucochef"


settings = Settings()
