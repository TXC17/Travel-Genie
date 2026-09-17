"""
Application Configuration and Environment Settings.
Uses Pydantic Settings for strict validation of runtime variables.
"""

from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    # Application Info
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "Travel Genie Backend"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # Server Networking
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Database
    DATABASE_URL: str = "sqlite:///./travel_genie.db"

    # Security & JWT Authentication
    SECRET_KEY: str = "dev_insecure_secret_key_change_in_production_9f83ac6b39"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Generative AI (Google Gemini) - Configurable, not hard-coded
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API Key")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash", description="Configurable Gemini Model")

    # Map Settings
    MAP_DEFAULT_LAT: float = 15.3350
    MAP_DEFAULT_LNG: float = 74.3188
    MAP_DEFAULT_ZOOM: int = 10

    # Algorithmic Weights (MCDM Recommender Engine)
    WEIGHT_INTEREST: float = 0.35
    WEIGHT_SEASON: float = 0.25
    WEIGHT_POPULARITY: float = 0.15
    WEIGHT_RATING: float = 0.15
    WEIGHT_BUDGET: float = 0.10

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
