"""Store chunk vectors in Qdrant, search them, and delete them by file."""
import uuid
from dataclasses import dataclass

from loguru import logger
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from app.core.exceptions import ExternalServiceError
from app.services.chunker import Chunk


# Fixed namespace so the same chunk always gets the same point ID.
_POINT_NAMESPACE = uuid.UUID("6f1c5a52-8a0e-4c1e-9b39-2f6d8e7f4a10")
_QDRANT_ERRORS = (UnexpectedResponse, ResponseHandlingException, ConnectionError, TimeoutError)


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    source: str
    page: int
    score: float


class QdrantVectorStore:
    UPSERT_BATCH_SIZE = 128

    def __init__(self, client: QdrantClient, collection: str, dimension: int):
        self._client = client
        self._collection = collection
        self._dimension = dimension

    def ensure_collection(self) -> None:
        """Create the collection on first use; check its vector size otherwise."""
        try:
            if self._client.collection_exists(self._collection):
                vectors = self._client.get_collection(self._collection).config.params.vectors
                existing = getattr(vectors, "size", None)
                if existing is not None and existing != self._dimension:
                    raise RuntimeError(
                        f"Qdrant collection '{self._collection}' stores {existing}-dimension vectors, "
                        f"but AZURE_OPENAI_EMBEDDING_MODEL_DIMENSION is {self._dimension}. "
                        "Use a new QDRANT_COLLECTION name or fix the dimension."
                    )
                return

            logger.info("Creating Qdrant collection '{}'", self._collection)
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=models.VectorParams(size=self._dimension, distance=models.Distance.COSINE),
            )
            # Index the file name so deleting a document's chunks is fast.
            self._client.create_payload_index(
                collection_name=self._collection,
                field_name="source",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
        except _QDRANT_ERRORS as exc:
            raise ExternalServiceError("Could not reach the vector database.") from exc

    def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("Each chunk needs exactly one vector")

        points = [
            models.PointStruct(
                id=str(uuid.uuid5(_POINT_NAMESPACE, f"{chunk.source}:{chunk.chunk_index}")),
                vector=vector,
                payload={
                    "text": chunk.text,
                    "source": chunk.source,
                    "page": chunk.page,
                    "chunk_index": chunk.chunk_index,
                },
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        try:
            for start in range(0, len(points), self.UPSERT_BATCH_SIZE):
                self._client.upsert(
                    collection_name=self._collection,
                    points=points[start:start + self.UPSERT_BATCH_SIZE],
                    wait=True,
                )
        except _QDRANT_ERRORS as exc:
            logger.exception("Qdrant upsert failed")
            raise ExternalServiceError("Could not save to the vector database.") from exc

    def search(self, vector: list[float], limit: int, min_score: float) -> list[RetrievedChunk]:
        try:
            response = self._client.query_points(
                collection_name=self._collection,
                query=vector,
                limit=limit,
                score_threshold=min_score,
                with_payload=True,
            )
        except _QDRANT_ERRORS as exc:
            logger.exception("Qdrant search failed")
            raise ExternalServiceError("Could not search the vector database.") from exc

        return [
            RetrievedChunk(
                text=point.payload["text"],
                source=point.payload["source"],
                page=point.payload["page"],
                score=point.score,
            )
            for point in response.points
        ]

    def delete_document(self, source: str) -> None:
        try:
            self._client.delete(
                collection_name=self._collection,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[models.FieldCondition(key="source", match=models.MatchValue(value=source))]
                    )
                ),
                wait=True,
            )
        except _QDRANT_ERRORS as exc:
            logger.exception("Qdrant delete failed")
            raise ExternalServiceError("Could not delete from the vector database.") from exc
