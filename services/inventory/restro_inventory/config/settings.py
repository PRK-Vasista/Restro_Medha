"""
File: settings.py
Purpose: Environment-driven configuration for the inventory microservice.
Responsibilities: Typed settings; no secrets in code.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Class: Settings
    Description: Inventory service configuration.

    Attributes:
        service_name, inventory_db_path, default_tenant_id, api_v1_prefix, log_json.

    Example usage:
        get_settings().inventory_db_path
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = Field(default="inventory", validation_alias="SERVICE_NAME")
    inventory_db_path: str = Field(default="/data/inventory.db", validation_alias="INVENTORY_DB_PATH")
    default_tenant_id: str = Field(default="default", validation_alias="DEFAULT_TENANT_ID")
    api_v1_prefix: str = Field(default="/v1", validation_alias="API_V1_PREFIX")
    log_json: bool = Field(default=True, validation_alias="LOG_JSON")


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
