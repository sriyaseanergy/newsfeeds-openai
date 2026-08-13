from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application settings.

    Add new settings fields here as capabilities grow.
    """

    app_name: str = "Editorial Intelligence Platform"
    app_version: str = "0.1.0"

    root_path: str = ""

    database_url: str = ""

    # OpenAI foundation settings (provider integration comes later).
    openai_api_key: str = ""
    openai_classification_model: str = "gpt-5-nano"
    openai_enrichment_model: str = "gpt-5-mini"
    openai_base_url: str | None = None
    classification_batch_size: int = 15

    # Microsoft Graph email settings.
    azure_tenant_id: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""
    graph_sender_email: str = ""
    graph_timeout_seconds: int = 30

    # Azure AD SPA authentication (ID token audience validation).
    azure_auth_client_id: str = ""

    # MyWork employee database (separate from application PostgreSQL).
    mywork_database_url: str = ""
    mywork_employee_table: str = "Employee"
    mywork_emp_no_column: str = "EmpNo"
    mywork_name_column: str = "Name"
    mywork_email_column: str = "Email"
    mywork_designation_column: str = "Designation"
    mywork_last_day_column: str = "LastDay"

    @field_validator("root_path", mode="before")
    @classmethod
    def normalize_root_path(cls, value: object) -> str:
        if value is None:
            return ""
        normalized = str(value).strip()
        if not normalized or normalized == "/":
            return ""
        return f"/{normalized.strip('/')}"

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

