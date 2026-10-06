from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    integrated_mode: Literal["local", "hosted"] = "local"
    integrated_synthetic_only: bool = True
    database_url: str = "postgresql+psycopg://pack_app:local-development-only@127.0.0.1:5432/pack"
    migration_database_url: str = ""
    auth_mode: str = "local"
    local_organization: str = "org_demo_alpha"
    local_operator: str = "local-operator"
    local_role: str = "supervisor"
    storage_mode: str = "local"
    storage_root: str = ".local/images"
    supabase_url: str = ""
    supabase_publishable_key: str = ""
    pack_organization: str = ""
    supabase_service_role_key: str = ""
    supabase_storage_bucket: str = "evidence"
    azure_storage_account_url: str = ""
    azure_storage_container: str = "evidence"
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = ""
    azure_openai_vision_deployment: str = ""
    azure_openai_api_key: str = ""
    model_provider: Literal["none", "ollama", "azure", "gemini"] = "none"
    gemini_api_key: str = ""
    gemini_model: str = ""
    gemini_free_tier_confirmed: bool = False
    hosted_model_review_required: bool = True
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = ""
    local_model_review_required: bool = True
    model_timeout_seconds: int = 45
    agent_mode: str = "batched"
    entra_tenant_id: str = ""
    entra_audience: str = ""
    entra_client_id: str = ""
    entra_scope: str = ""
    demo_enabled: bool = False
    demo_signing_secret: str = ""
    demo_ttl_hours: int = 24
    demo_daily_sessions: int = 25
    daily_model_limit: int = 100
    worker_enabled: bool = True
    allowed_origins: str = ""

    @property
    def provider_configured(self):
        if self.model_provider == "gemini":
            return bool(
                self.gemini_api_key
                and self.gemini_model == "gemini-2.5-flash"
                and self.gemini_free_tier_confirmed
            )
        if self.model_provider == "ollama":
            return bool(self.ollama_base_url and self.ollama_model)
        if self.model_provider != "azure":
            return False
        return all(
            (self.azure_openai_endpoint, self.azure_openai_api_version, self.azure_openai_vision_deployment)
        )


@lru_cache
def settings():
    return Settings()
