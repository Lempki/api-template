import logging
import logging.config
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI

from .auth import require_auth
from .config import Settings, get_settings
from .models import HealthResponse, TemplateRequest, TemplateResponse


def _configure_logging(level: str) -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "formatters": {
                "json": {
                    "format": (
                        '{"time":"%(asctime)s","level":"%(levelname)s",'
                        '"name":"%(name)s","message":"%(message)s"}'
                    )
                }
            },
            "handlers": {
                "console": {"class": "logging.StreamHandler", "formatter": "json"}
            },
            "root": {"level": level, "handlers": ["console"]},
        }
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    _configure_logging(settings.log_level)
    # Add startup logic here (e.g. load a model, open a database connection).
    yield
    # Add shutdown logic here (e.g. close connections).


app = FastAPI(title="discord-api-template", version="1.0.0", lifespan=lifespan)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="discord-api-template", version="1.0.0")


# Template endpoint — rename the path and replace the implementation with your own.
# Remove the Depends(require_auth) import from models.py once you no longer need this example.
@app.post(
    "/template/echo",
    response_model=TemplateResponse,
    dependencies=[Depends(require_auth)],
)
async def echo(
    body: TemplateRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> TemplateResponse:
    return TemplateResponse(text=body.text)
