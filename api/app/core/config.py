from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    log_level: str = "INFO"

    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "chunks_v1"

    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_timeout_s: int = 300

    fast_model: str = "phi3:mini"
    quality_model: str = "qwen2.5:32b"
    quality_fallback_models: str = "llama3.1:8b-instruct,deepseek-r1-distill-qwen:7b"

    llm_provider: str = "ollama"  # ollama or nvidia

    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_api_key: str = ""  # set it in the .env file
    nvidia_fast_model: str = "moonshotai/kimi-k2-thinking"
    nvidia_quality_model: str = "nvidia/llama-3.1-nemotron-ultra-253b-v1"

    sqlite_path: str = "/app/data/app.db"

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_batch_size: int = 32

    enable_rerank: bool = True
    rerank_model: str = "BAAI/bge-reranker-base"
    rerank_candidates: int = 20  # qdrant fetch N, rerank top N -> return top_k


settings = Settings()
