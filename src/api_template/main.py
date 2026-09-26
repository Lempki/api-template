"""The FastAPI application, its lifespan, and its routes."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from .auth import require_auth
from .config import get_settings
from .logging_config import configure_logging
from .models import HealthResponse, TemplateRequest, TemplateResponse
from .service import service_version

# The service name is also the project name in pyproject.toml, which the version is read from.
SERVICE = "discord-api-template"
VERSION = service_version(SERVICE)

# Logging is set up on import, before uvicorn prints its startup lines, so every line is JSON.
configure_logging(get_settings().log_level)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Runs startup work before the first request and shutdown work after the last one."""
    # Open connections or load models here.
    yield
    # Close them here.


app = FastAPI(title=SERVICE, version=VERSION, lifespan=lifespan)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Reports that the service is up. It needs no token, so monitors and Docker can call it."""
    return HealthResponse(status="ok", service=SERVICE, version=VERSION)


# The example endpoint. Rename its path and replace its body with your own.
# Every route except /health should keep the require_auth dependency.
@app.post(
    "/template/echo",
    response_model=TemplateResponse,
    dependencies=[Depends(require_auth)],
)
async def echo(body: TemplateRequest) -> TemplateResponse:
    """Returns the text it receives."""
    return TemplateResponse(text=body.text)
