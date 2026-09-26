"""Request and response models."""

from pydantic import BaseModel

__all__ = ["HealthResponse", "TemplateRequest", "TemplateResponse"]


class HealthResponse(BaseModel):
    """The body of GET /health."""

    status: str
    service: str
    version: str


# The example endpoint's models. Rename or replace them with your own.


class TemplateRequest(BaseModel):
    """The body of the example endpoint."""

    text: str


class TemplateResponse(BaseModel):
    """The reply of the example endpoint."""

    text: str
