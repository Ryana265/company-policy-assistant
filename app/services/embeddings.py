"""Turn text into vectors with Azure OpenAI."""
from typing import Protocol

import openai
from loguru import logger
from openai import AzureOpenAI

from app.core.exceptions import ExternalServiceError


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class AzureOpenAIEmbedder:
    BATCH_SIZE = 64  # texts per request

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        api_version: str,
        deployment: str,
        dimension: int,
    ):
        self._client = AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version=api_version)
        self._deployment = deployment
        self._dimension = dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self.BATCH_SIZE):
            batch = texts[start:start + self.BATCH_SIZE]
            try:
                response = self._client.embeddings.create(
                    model=self._deployment,
                    input=batch,
                    dimensions=self._dimension,
                )
            except openai.APIError as exc:
                logger.exception("Azure OpenAI embedding request failed")
                raise ExternalServiceError("Embedding service failed. Try again later.") from exc
            # Sort by index so vectors always line up with their input text.
            vectors.extend(item.embedding for item in sorted(response.data, key=lambda d: d.index))
        return vectors
