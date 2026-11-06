"""Errors the services raise. main.py turns each one into an HTTP response,
so services never need to know about FastAPI or status codes."""


class PolicyAssistantError(Exception):
    status_code = 500

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InvalidDocumentError(PolicyAssistantError):
    status_code = 400


class DocumentNotFoundError(PolicyAssistantError):
    status_code = 404


class DocumentExistsError(PolicyAssistantError):
    status_code = 409


class DocumentTooLargeError(PolicyAssistantError):
    status_code = 413


class NoTextFoundError(PolicyAssistantError):
    status_code = 422


class ExternalServiceError(PolicyAssistantError):
    """Azure OpenAI, Qdrant or Claude failed or could not be reached."""
    status_code = 502
