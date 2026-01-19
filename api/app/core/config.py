from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    log_level: str = "INFO"

    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "chunks_v1"

    ollama_base_url: str = "http://host.docker.internal:11434"
    fast_model: str = "phi3:mini"
    quality_model: str = "qwen2.5:7b-instruct "

    sqlite_path: str = "/app/data/app.db"

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_batch_size: int = 32


settings = Settings()
