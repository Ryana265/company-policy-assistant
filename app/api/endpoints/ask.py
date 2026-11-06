from fastapi import APIRouter, Depends

from app.api.dependencies import get_qa_service
from app.schemas.ask import AskRequest, AskResponse, CitationOut
from app.services.qa import QAService

router = APIRouter()


@router.post("", response_model=AskResponse)
def ask(request: AskRequest, service: QAService = Depends(get_qa_service)):
    """Answer a question from the uploaded policies, with [n] citations."""
    result = service.ask(request.question.strip())
    return AskResponse(
        answer=result.answer,
        covered=result.covered,
        citations=[
            CitationOut(id=c.id, source=c.source, page=c.page, score=c.score) for c in result.citations
        ],
    )
