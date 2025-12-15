"""
Configuration management using Pydantic settings.

Loads environment variables and provides typed configuration access.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Supabase
    supabase_url: str
    supabase_service_role_key: str
    supabase_anon_key: str = ""  # Optional for backend
    supabase_jwks_url: str = ""  # Will be derived from supabase_url if not set

    # OpenAI
    openai_api_key: str

    # OCR
    ocr_api_url: str = ""  # Empty for stub mode
    ocr_api_token: str = ""

    # Admin
    admin_api_key: str

    # Application
    env: str = "dev"  # dev, staging, prod
    cors_origins: str = "http://localhost:5173"  # Comma-separated

    # Derived properties
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_dev(self) -> bool:
        """Check if running in development mode."""
        return self.env == "dev"

    @property
    def use_stub_ocr(self) -> bool:
        """Use stub OCR client in development."""
        return self.is_dev and not self.ocr_api_url

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()
