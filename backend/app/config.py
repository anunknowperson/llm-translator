from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres
    postgres_user: str = "translator"
    postgres_password: str = "translator"
    postgres_db: str = "translator"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_broker_db: int = 0
    redis_backend_db: int = 1

    # vLLM / ML
    model_name: str = "Qwen/Qwen3.5-0.8B"
    vllm_host: str = "vllm"
    vllm_port: int = 8000
    ml_max_new_tokens: int = 1024
    ml_request_timeout: int = 120

    # Backend
    log_level: str = "INFO"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_broker_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_broker_db}"

    @property
    def redis_backend_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_backend_db}"

    @property
    def vllm_base_url(self) -> str:
        return f"http://{self.vllm_host}:{self.vllm_port}/v1"


settings = Settings()
