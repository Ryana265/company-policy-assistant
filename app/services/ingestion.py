"""Upload pipeline: validate -> save -> read -> chunk -> embed -> store in Qdrant."""
from dataclasses import dataclass

from loguru import logger

from app.core.exceptions import (
    DocumentExistsError,
    DocumentNotFoundError,
    DocumentTooLargeError,
    InvalidDocumentError,
    NoTextFoundError,
)
from app.services.chunker import chunk_pages
from app.services.document_store import DocumentStore
from app.services.embeddings import Embedder
from app.services.pdf_loader import load_pdf
from app.services.vector_store import QdrantVectorStore


@dataclass(frozen=True)
class IngestResult:
    filename: str
    pages: int
    chunks: int


class IngestionService:
    def __init__(
        self,
        documents: DocumentStore,
        embedder: Embedder,
        vector_store: QdrantVectorStore,
        max_upload_bytes: int,
        chunk_size_words: int,
        chunk_overlap_words: int,
    ):
        self._documents = documents
        self._embedder = embedder
        self._vector_store = vector_store
        self.max_upload_bytes = max_upload_bytes
        self._chunk_size = chunk_size_words
        self._chunk_overlap = chunk_overlap_words

    def ingest(self, filename: str, content: bytes) -> IngestResult:
        name = self._documents.safe_name(filename)
        self._validate(name, content)
        if self._documents.exists(name):
            raise DocumentExistsError(f"'{name}' already exists. Delete it first to replace it.")

        path = self._documents.save(name, content)
        try:
            pages = load_pdf(path)
            if not pages:
                raise NoTextFoundError("No text found in this PDF. It may be a scanned image that needs OCR.")

            chunks = chunk_pages(pages, self._chunk_size, self._chunk_overlap)
            vectors = self._embedder.embed([chunk.text for chunk in chunks])
            self._vector_store.upsert(chunks, vectors)
        except Exception:
            # Undo everything so a failed upload leaves no file and no half-stored chunks.
            self._rollback(name)
            raise

        logger.info("Ingested {}: {} pages, {} chunks", name, len(pages), len(chunks))
        return IngestResult(filename=name, pages=len(pages), chunks=len(chunks))

    def delete(self, filename: str) -> None:
        name = self._documents.safe_name(filename)
        if not self._documents.exists(name):
            raise DocumentNotFoundError(f"'{name}' not found")
        # Remove the chunks first: if Qdrant fails, the file stays and the delete can be retried.
        self._vector_store.delete_document(name)
        self._documents.delete(name)
        logger.info("Deleted {}", name)

    def _validate(self, name: str, content: bytes) -> None:
        if not name.lower().endswith(".pdf"):
            raise InvalidDocumentError("Only PDF files are accepted")
        if len(content) > self.max_upload_bytes:
            raise DocumentTooLargeError(
                f"File is larger than {self.max_upload_bytes // (1024 * 1024)} MB"
            )
        if not content.startswith(b"%PDF"):
            raise InvalidDocumentError("File is not a valid PDF")

    def _rollback(self, name: str) -> None:
        try:
            self._vector_store.delete_document(name)
        except Exception:
            logger.exception("Rollback: could not remove chunks for {} from Qdrant", name)
        try:
            self._documents.delete(name)
        except DocumentNotFoundError:
            pass
