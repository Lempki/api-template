from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


# Template request and response models — rename or replace with your own.


class TemplateRequest(BaseModel):
    text: str


class TemplateResponse(BaseModel):
    text: str
