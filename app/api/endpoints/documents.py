from fastapi import APIRouter, Depends, Response, UploadFile, status
from app.api.dependencies import get_document_store, get_ingestion_service
from app.schemas.documents import DocumentListResponse, DocumentUploadResponse
from app.services.document_store import DocumentStore
from app.services.ingestion import IngestionService

router = APIRouter()

@router.post("", status_code=status.HTTP_201_CREATED, response_model=DocumentUploadResponse)
def upload_document(file: UploadFile, service: IngestionService = Depends(get_ingestion_service)):
    """Upload a policy PDF. It is saved, split into chunks, embedded and stored in Qdrant."""
    # Read one byte past the limit: enough to detect an oversized file without reading all of it.
    content = file.file.read(service.max_upload_bytes + 1)
    result = service.ingest(file.filename or "", content)
    return DocumentUploadResponse(filename=result.filename, pages=result.pages, chunks=result.chunks)


@router.get("", response_model=DocumentListResponse)
def list_documents(documents: DocumentStore = Depends(get_document_store)):
    return DocumentListResponse(documents=documents.list())


@router.delete("/{filename}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(filename: str, service: IngestionService = Depends(get_ingestion_service)):
    """Delete a PDF and all of its chunks from Qdrant."""
    service.delete(filename)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
