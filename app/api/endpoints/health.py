from fastapi import APIRouter

router = APIRouter()


@router.get("")
def health():
    """Liveness check: the app is running."""
    return {"status": "ok"}
