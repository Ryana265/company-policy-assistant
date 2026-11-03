"""Loads settings from .env into one typed object.

Every other module calls get_settings() rather than reading os.environ directly,
so a missing key is reported once, clearly, at startup.
"""
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # reads .env from the current working directory

DEPARTMENTS = ("hr", "it", "finance")


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required setting '{name}' in .env")
    return value


@dataclass(frozen=True)
class Settings:
    # Azure OpenAI embeddings
    embedding_endpoint: str
    embedding_api_key: str
    embedding_deployment: str
    embedding_api_version: str
    embedding_dimension: int

    # Qdrant
    qdrant_url: str
    qdrant_api_key: str
    qdrant_collection: str

    # Claude (Azure AI Foundry)
    claude_endpoint: str
    claude_api_key: str
    claude_model: str

    # App
    data_dir: Path
    top_k: int
    min_score: float

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            embedding_endpoint=_require("AZURE_OPENAI_EMBEDDING_ENDPOINT"),
            embedding_api_key=_require("AZURE_OPENAI_EMBEDDING_API_KEY"),
            embedding_deployment=_require("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
            embedding_api_version=_require("AZURE_OPENAI_EMBEDDING_API_VERSION"),
            embedding_dimension=int(_require("AZURE_OPENAI_EMBEDDING_MODEL_DIMENSION")),
            qdrant_url=_require("QDRANT_URL"),
            qdrant_api_key=_require("QDRANT_API_KEY"),
            qdrant_collection=_require("QDRANT_COLLECTION"),
            claude_endpoint=_require("CLAUDE_ENDPOINT"),
            claude_api_key=_require("CLAUDE_API_KEY"),
            claude_model=_require("CLAUDE_MODEL"),
            data_dir=Path(os.getenv("DATA_DIR", "data")),
            top_k=int(os.getenv("TOP_K", "5")),
            min_score=float(os.getenv("MIN_SCORE", "0.30")),
        )


@lru_cache  # build Settings once, reuse it everywhere
def get_settings() -> Settings:
    return Settings.from_env()
