from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application settings.

    Add new settings fields here as capabilities grow.
    """

    app_name: str = "Editorial Intelligence Platform"
    app_version: str = "0.1.0"

    database_url: str = ""

    # OpenAI foundation settings (provider integration comes later).
    openai_api_key: str = ""
    openai_classification_model: str = "gpt-5-nano"
    openai_enrichment_model: str = "gpt-5-mini"
    openai_base_url: str | None = None

    # Microsoft Graph email settings.
    azure_tenant_id: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""
    graph_sender_email: str = ""
    graph_timeout_seconds: int = 30

    @property
    def openai_model(self) -> str:
        """
        Backward-compatible alias for existing integrations.
        Defaults to the classification model.
        """
        return self.openai_classification_model

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

