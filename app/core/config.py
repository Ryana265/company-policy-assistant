from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # Project
    PROJECT_NAME: str = "Company Policy Assistant"
    PROJECT_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    ENVIRONMENT: str = "local"
    LOG_LEVEL: str = "INFO"

    # Azure OpenAI Embeddings
    AZURE_OPENAI_EMBEDDING_ENDPOINT: str
    AZURE_OPENAI_EMBEDDING_API_KEY: str
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str
    AZURE_OPENAI_EMBEDDING_API_VERSION: str
    AZURE_OPENAI_EMBEDDING_MODEL_DIMENSION: int

    # Qdrant
    QDRANT_URL: str
    QDRANT_API_KEY: str
    QDRANT_COLLECTION: str

    # Claude (Azure AI Foundry)
    CLAUDE_ENDPOINT: str
    CLAUDE_API_KEY: str
    CLAUDE_MODEL: str
    CLAUDE_MAX_TOKENS: int = 4096

    # Documents
    DATA_DIR: Path = Path("data")  # where uploaded policy PDFs are saved
    MAX_UPLOAD_MB: int = 20

    # Chunking
    CHUNK_SIZE_WORDS: int = 300
    CHUNK_OVERLAP_WORDS: int = 50

    # Retrieval
    TOP_K: int = 5           # how many chunks to send to Claude
    MIN_SCORE: float = 0.30  # below this, the policy is treated as not covering the question

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    @model_validator(mode="after")
    def check_chunking(self) -> "Settings":
        if not 0 <= self.CHUNK_OVERLAP_WORDS < self.CHUNK_SIZE_WORDS:
            raise ValueError("CHUNK_OVERLAP_WORDS must be at least 0 and smaller than CHUNK_SIZE_WORDS")
        return self


settings = Settings()
