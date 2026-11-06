"""Builds each client once and hands it to the routes."""
from functools import lru_cache

from fastapi import Depends
from qdrant_client import QdrantClient

from app.core.config import settings
from app.services.document_store import DocumentStore
from app.services.embeddings import AzureOpenAIEmbedder, Embedder
from app.services.ingestion import IngestionService
from app.services.llm import Answerer, ClaudeAnswerer
from app.services.qa import QAService
from app.services.vector_store import QdrantVectorStore


@lru_cache
def get_document_store() -> DocumentStore:
    return DocumentStore(settings.DATA_DIR)


@lru_cache
def get_embedder() -> Embedder:
    return AzureOpenAIEmbedder(
        endpoint=settings.AZURE_OPENAI_EMBEDDING_ENDPOINT,
        api_key=settings.AZURE_OPENAI_EMBEDDING_API_KEY,
        api_version=settings.AZURE_OPENAI_EMBEDDING_API_VERSION,
        deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        dimension=settings.AZURE_OPENAI_EMBEDDING_MODEL_DIMENSION,
    )


@lru_cache
def get_vector_store() -> QdrantVectorStore:
    store = QdrantVectorStore(
        client=QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY),
        collection=settings.QDRANT_COLLECTION,
        dimension=settings.AZURE_OPENAI_EMBEDDING_MODEL_DIMENSION,
    )
    store.ensure_collection()
    return store


@lru_cache
def get_answerer() -> Answerer:
    return ClaudeAnswerer(
        endpoint=settings.CLAUDE_ENDPOINT,
        api_key=settings.CLAUDE_API_KEY,
        model=settings.CLAUDE_MODEL,
        max_tokens=settings.CLAUDE_MAX_TOKENS,
    )


def get_ingestion_service(
    documents: DocumentStore = Depends(get_document_store),
    embedder: Embedder = Depends(get_embedder),
    vector_store: QdrantVectorStore = Depends(get_vector_store),
) -> IngestionService:
    return IngestionService(
        documents=documents,
        embedder=embedder,
        vector_store=vector_store,
        max_upload_bytes=settings.MAX_UPLOAD_MB * 1024 * 1024,
        chunk_size_words=settings.CHUNK_SIZE_WORDS,
        chunk_overlap_words=settings.CHUNK_OVERLAP_WORDS,
    )


def get_qa_service(
    embedder: Embedder = Depends(get_embedder),
    vector_store: QdrantVectorStore = Depends(get_vector_store),
    answerer: Answerer = Depends(get_answerer),
) -> QAService:
    return QAService(
        embedder=embedder,
        vector_store=vector_store,
        answerer=answerer,
        top_k=settings.TOP_K,
        min_score=settings.MIN_SCORE,
    )
