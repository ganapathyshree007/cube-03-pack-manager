from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://pack_app:local-development-only@127.0.0.1:5432/pack"
    migration_database_url: str = ""
    auth_mode: str = "local"
    local_organization: str = "org_demo_alpha"
    local_operator: str = "local-operator"
    local_role: str = "supervisor"
    storage_mode: str = "local"
    storage_root: str = ".local/images"
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_storage_bucket: str = "evidence"
    azure_storage_account_url: str = ""
    azure_storage_container: str = "evidence"
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = ""
    azure_openai_vision_deployment: str = ""
    azure_openai_api_key: str = ""
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

    @property
    def provider_configured(self):
        return all(
            (self.azure_openai_endpoint, self.azure_openai_api_version, self.azure_openai_vision_deployment)
        )


@lru_cache
def settings():
    return Settings()
