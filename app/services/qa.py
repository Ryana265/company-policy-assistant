"""Question pipeline: embed question -> search Qdrant -> Claude answers with citations."""
import re
from dataclasses import dataclass

from app.services.embeddings import Embedder
from app.services.llm import NOT_COVERED_ANSWER, Answerer
from app.services.vector_store import QdrantVectorStore, RetrievedChunk

_CITATION = re.compile(r"\[(\d+)\]")


@dataclass(frozen=True)
class Citation:
    id: int
    source: str
    page: int
    score: float


@dataclass(frozen=True)
class QAResult:
    answer: str
    covered: bool
    citations: list[Citation]


class QAService:
    def __init__(
        self,
        embedder: Embedder,
        vector_store: QdrantVectorStore,
        answerer: Answerer,
        top_k: int,
        min_score: float,
    ):
        self._embedder = embedder
        self._vector_store = vector_store
        self._answerer = answerer
        self._top_k = top_k
        self._min_score = min_score

    def ask(self, question: str) -> QAResult:
        [query_vector] = self._embedder.embed([question])
        chunks = self._vector_store.search(query_vector, limit=self._top_k, min_score=self._min_score)

        # Nothing relevant enough: don't spend a Claude call, and don't let it guess.
        if not chunks:
            return QAResult(answer=NOT_COVERED_ANSWER, covered=False, citations=[])

        answer = self._answerer.answer(question, chunks)
        citations = _cited_sources(answer, chunks)
        covered = bool(citations) and NOT_COVERED_ANSWER not in answer
        return QAResult(answer=answer, covered=covered, citations=citations)


def _cited_sources(answer: str, chunks: list[RetrievedChunk]) -> list[Citation]:
    """Return only the sources Claude actually cited, ignoring numbers that don't exist."""
    cited_ids = sorted({int(n) for n in _CITATION.findall(answer) if 1 <= int(n) <= len(chunks)})
    return [
        Citation(id=i, source=chunks[i - 1].source, page=chunks[i - 1].page, score=round(chunks[i - 1].score, 4))
        for i in cited_ids
    ]
