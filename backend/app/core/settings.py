from functools import lru_cache

from app.scheduling.ist_schedule import parse_ist_time_of_day, parse_weekly_digest_day
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

    # Newsletter digest scheduler (IST / Asia/Kolkata).
    daily_digest_time: str = "08:00"
    weekly_digest_day: str = "Friday"
    weekly_digest_time: str = "08:00"
    scheduler_enabled: bool = True
    digest_max_articles_per_feed: int = 10

    # Employee SPA authentication. SPA -> Azure AD ID token -> authenticated user.
    # Env: AZURE_TENANT_ID, AZURE_AUTH_CLIENT_ID
    azure_tenant_id: str = ""
    azure_auth_client_id: str = ""

    # Comma-separated emails allowed to manage feed sources (POST/PUT/DELETE /feeds).
    feed_source_admin_emails: str = ""

    # Microsoft Graph delegated Mail.Send for newsletters.
    # News Feeds backend -> delegated MSAL token -> Graph Mail.Send
    # -> GRAPH_SENDER_EMAIL (e.g. broadcast@seanergy.ai).
    # Uses AZURE_TENANT_ID + AZURE_CLIENT_ID + AZURE_CLIENT_SECRET.
    # The Azure app is a confidential client, so device-code token
    # exchange must include the secret (AADSTS7000218 otherwise).
    # Do not reuse AZURE_AUTH_CLIENT_ID (that is employee SPA login only).
    azure_client_id: str = ""
    azure_client_secret: str = ""
    graph_sender_email: str = ""
    graph_timeout_seconds: int = 30
    redirect_uri: str = ""   # env: REDIRECT_URI
    graph_token_cache_path: str = "data/config/graph_msal_token_cache.bin"

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

    @field_validator(
        "azure_tenant_id",
        "azure_client_id",
        "azure_client_secret",
        "azure_auth_client_id",
        "graph_sender_email",
        mode="before",
    )
    @classmethod
    def strip_quoted_env_value(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value).strip().strip('"').strip("'")

    @field_validator("daily_digest_time", "weekly_digest_time", mode="before")
    @classmethod
    def normalize_digest_time(cls, value: object) -> str:
        if value is None:
            return "08:00"
        normalized = str(value).strip()
        if not normalized:
            return "08:00"
        return normalized

    @field_validator("weekly_digest_day", mode="before")
    @classmethod
    def normalize_weekly_digest_day(cls, value: object) -> str:
        if value is None:
            return "Friday"
        normalized = str(value).strip()
        if not normalized:
            return "Friday"
        return normalized.title()

    @field_validator("daily_digest_time", "weekly_digest_time", mode="after")
    @classmethod
    def validate_digest_time(cls, value: str, info) -> str:
        parse_ist_time_of_day(value, field_name=str(info.field_name))
        return value

    @field_validator("weekly_digest_day", mode="after")
    @classmethod
    def validate_weekly_digest_day(cls, value: str) -> str:
        parse_weekly_digest_day(value)
        return value

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

