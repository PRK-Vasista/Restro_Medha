"""
File: settings.py
Purpose: Central, environment-driven configuration (SaaS-ready, no hardcoded secrets).
Responsibilities: Load .env / OS env; expose typed settings for services and persistence.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Class: Settings
    Description: Application configuration loaded from environment variables.

    Attributes:
        service_name: Logical name for logs and metrics.
        billing_db_path: SQLite file path for edge persistence.
        default_tenant_id: Fallback when X-Tenant-Id header is absent.
        gst_combined_rate: Combined GST rate as decimal (e.g. 0.05 for 5%).
        api_v1_prefix: First-class API version prefix.

    Example usage:
        s = get_settings()
        print(s.billing_db_path)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # Allow Settings(billing_db_path="...") in tests; env still uses SERVICE_NAME-style aliases
        populate_by_name=True,
    )

    service_name: str = Field(default="billing", validation_alias="SERVICE_NAME")
    billing_db_path: str = Field(default="/data/billing.db", validation_alias="BILLING_DB_PATH")
    default_tenant_id: str = Field(default="default", validation_alias="DEFAULT_TENANT_ID")
    gst_combined_rate: float = Field(default=0.05, ge=0.0, le=1.0, validation_alias="GST_COMBINED_RATE")
    api_v1_prefix: str = Field(default="/v1", validation_alias="API_V1_PREFIX")
    log_json: bool = Field(default=True, validation_alias="LOG_JSON")


@lru_cache
def get_settings() -> Settings:
    """
    Description: Cached singleton for settings (avoids re-parsing env on every request).

    Inputs:
        None

    Outputs:
        Settings: Frozen configuration snapshot.

    Exceptions raised:
        ValidationError: If environment values fail validation.
    """
    return Settings()
