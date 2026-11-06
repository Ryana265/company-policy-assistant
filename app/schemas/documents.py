from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    filename: str
    pages: int
    chunks: int


class DocumentListResponse(BaseModel):
    documents: list[str]
