from dotools.sdk import AppConfig
from pathlib import Path


def create_settings(env_vars: list[str], *, deps: AppConfig) -> None:
    fields = "\n".join(f"    {name.lower()}: str" for name in env_vars)

    code = f"""from functools import cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
{fields}


@cache
def get_settings() -> Settings:
    return Settings()  # ty:ignore[missing-argument]


if __name__ == "__main__":
    settings = get_settings()
    print(settings)
"""

    package_dir = next(
        p for p in Path("src").iterdir() if p.is_dir() and not p.name.startswith(".")
    )

    settings_file = package_dir / "__settings.py"

    deps.helper.ask_text_to_path(settings_file, code)
