from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    llm_api_key: str = ""
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "qwen-plus"
    smtp_host: str = "smtp.qq.com"
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    email_to: str = ""
    cron_hour: int = 9
    cron_minute: int = 0
    github_token: str = ""
    trending_languages: str = "python,javascript,typescript,vue,go,rust"
    trending_since: str = "daily"
    max_projects: int = 25
    dedup_days: int = 7
    database_url: str = "postgresql://trending:trending_secret@localhost:5432/trending"
    redis_url: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
