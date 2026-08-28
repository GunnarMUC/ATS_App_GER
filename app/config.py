from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_host: str = "127.0.0.1"
    app_port: int = 8000
    ollama_host: str = "http://127.0.0.1:11434"
    ollama_model_strong: str = "qwen2.5:14b"
    ollama_model_fast: str = "qwen2.5:7b"
    ollama_allow_nonlocal: bool = False
    app_allow_nonlocal: bool = False
    data_dir: Path = Path("./data")
    max_upload_mb: int = 8
    llm_timeout_s: int = 180
    debug: bool = False
    database_url: str = ""

    @field_validator("app_host")
    @classmethod
    def warn_non_loopback_bind(cls, v: str) -> str:
        return v.strip() or "127.0.0.1"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def generated_dir(self) -> Path:
        return self.data_dir / "generated"

    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        db_path = (self.data_dir / "ats_app.db").resolve()
        return f"sqlite:///{db_path}"

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        (self.generated_dir / "cv").mkdir(parents=True, exist_ok=True)
        (self.generated_dir / "cover").mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s


def is_loopback_host(url: str) -> bool:
    parsed = urlparse(url if "://" in url else f"http://{url}")
    host = (parsed.hostname or "").lower()
    return host in {"127.0.0.1", "localhost", "::1"}
