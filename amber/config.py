"""配置：多一个两周可用工时。"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="AMBER_", extra="ignore")

    db_path: Path = Path("data/amber.db")
    port: int = 8005
    llm_base_url: str = "https://api.deepseek.com"
    llm_api_key: str = ""
    llm_model: str = "deepseek-flash"
    llm_timeout: float = 30.0
    webhook_url: str = ""
    TZ: str = "Asia/Shanghai"
    capacity_hours: float = 40.0

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_api_key)


settings = Settings()
