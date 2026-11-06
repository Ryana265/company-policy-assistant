"""Keep the original uploaded PDFs on disk, so they can be re-processed later."""
from pathlib import Path

from app.core.exceptions import DocumentNotFoundError, InvalidDocumentError


class DocumentStore:
    def __init__(self, directory: Path):
        self._directory = directory

    def safe_name(self, filename: str) -> str:
        # Drop any folders so a name like "../../x.pdf" can't escape the directory.
        name = Path(filename).name
        if not name or name.startswith("."):
            raise InvalidDocumentError("Invalid file name")
        return name

    def exists(self, filename: str) -> bool:
        return (self._directory / self.safe_name(filename)).exists()

    def path(self, filename: str) -> Path:
        return self._directory / self.safe_name(filename)

    def save(self, filename: str, content: bytes) -> Path:
        self._directory.mkdir(parents=True, exist_ok=True)
        path = self.path(filename)
        path.write_bytes(content)
        return path

    def list(self) -> list[str]:
        if not self._directory.exists():
            return []
        return [p.name for p in sorted(self._directory.glob("*.pdf"))]

    def delete(self, filename: str) -> None:
        path = self.path(filename)
        if not path.exists():
            raise DocumentNotFoundError(f"'{path.name}' not found")
        path.unlink()
