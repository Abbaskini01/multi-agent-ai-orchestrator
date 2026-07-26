"""
Neural Glass AI Orchestrator — Fail-Fast Configuration Management
"""

import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    app_name: str = Field(default="Neural Glass AI Orchestrator", env="APP_NAME")
    app_version: str = Field(default="4.2.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    app_env: str = Field(default="production", env="APP_ENV")

    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")

    gemini_api_key: str = Field(default="", env="GEMINI_API_KEY")
    groq_api_key: str = Field(default="", env="GROQ_API_KEY")
    default_gemini_model: str = Field(default="gemini-2.5-flash", env="DEFAULT_GEMINI_MODEL")
    default_groq_model: str = Field(default="llama-3.3-70b-versatile", env="DEFAULT_GROQ_MODEL")
    enable_llm_streaming: bool = Field(default=True, env="ENABLE_LLM_STREAMING")

    workspace_dir: Path = Field(default=Path(__file__).parent.parent / "workspace_sandbox", env="WORKSPACE_DIR")
    sqlite_db_name: str = Field(default="app.db", env="SQLITE_DB_NAME")

    ws_ping_interval: float = Field(default=20.0, env="WS_PING_INTERVAL")
    ws_max_connections: int = Field(default=100, env="WS_MAX_CONNECTIONS")
    ws_timeout_seconds: float = Field(default=60.0, env="WS_TIMEOUT_SECONDS")

    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    json_logging: bool = Field(default=True, env="JSON_LOGGING")

    max_api_retries: int = Field(default=3, env="MAX_API_RETRIES")
    retry_delay_seconds: float = Field(default=1.0, env="RETRY_DELAY_SECONDS")
    retry_exponential_multiplier: float = Field(default=2.0, env="RETRY_EXPONENTIAL_MULTIPLIER")

    request_timeout_seconds: float = Field(default=30.0, env="REQUEST_TIMEOUT_SECONDS")
    streaming_timeout_seconds: float = Field(default=120.0, env="STREAMING_TIMEOUT_SECONDS")

    dlp_enabled: bool = Field(default=True, env="DLP_ENABLED")
    secret_scanning_enabled: bool = Field(default=True, env="SECRET_SCANNING_ENABLED")

    @field_validator("app_env")

    def validate_app_env(cls, v: str) -> str:
        allowed = ["development", "testing", "staging", "production"]
        if v.lower() not in allowed:
            raise ValueError(f"Invalid APP_ENV: '{v}'. Must be one of {allowed}")
        return v.lower()

    @field_validator("request_timeout_seconds", "ws_timeout_seconds")

    def validate_positive_timeouts(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Timeouts must be greater than 0 seconds.")
        return v

    def validate_startup_credentials(self) -> None:
        """Fail-fast checks invoked on application startup."""
        if self.app_env == "production":
            if not self.groq_api_key and not self.gemini_api_key:
                raise RuntimeError("CRITICAL STARTUP ERROR: At least one LLM API key (GROQ or GEMINI) is required in production mode.")

        try:
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"CRITICAL STARTUP ERROR: Unable to create workspace directory at {self.workspace_dir}: {e}")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()