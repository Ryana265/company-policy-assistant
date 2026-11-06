from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import PolicyAssistantError
from app.core.logging import setup_logging


def create_app() -> FastAPI:
    setup_logging(settings.LOG_LEVEL)

    app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

    @app.exception_handler(PolicyAssistantError)
    def handle_app_error(_: Request, exc: PolicyAssistantError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    app.include_router(api_router, prefix=settings.API_PREFIX)

    return app


app = create_app()
