"""Split pages into overlapping word windows.

Chunks never cross a page boundary, so every chunk has exactly one page to cite.
"""
from dataclasses import dataclass

from app.services.pdf_loader import Page


@dataclass(frozen=True)
class Chunk:
    text: str
    source: str
    page: int
    chunk_index: int  # position within the document, unique per source


def chunk_pages(pages: list[Page], size_words: int, overlap_words: int) -> list[Chunk]:
    if not 0 <= overlap_words < size_words:
        raise ValueError("overlap_words must be at least 0 and smaller than size_words")

    step = size_words - overlap_words
    chunks: list[Chunk] = []
    for page in pages:
        words = page.text.split()
        for start in range(0, len(words), step):
            window = words[start:start + size_words]
            chunks.append(
                Chunk(
                    text=" ".join(window),
                    source=page.source,
                    page=page.page,
                    chunk_index=len(chunks),
                )
            )
            if start + size_words >= len(words):
                break  # this window reached the end of the page
    return chunks
