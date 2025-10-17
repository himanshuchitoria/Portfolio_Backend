from pydantic import Field, AnyUrl, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables or defaults.
    """

  
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")

    # MongoDB connection URL
    mongodb_uri: AnyUrl = Field(..., env="MONGODB_URI")

    # Session expiration in minutes 
    session_expiration_minutes: int = Field(1440, env="SESSION_EXPIRATION_MINUTES")

    # Allowed CORS origins, 
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"])

    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
