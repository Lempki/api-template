# api-template

This is a clean and minimal Python REST API template built with [FastAPI](https://fastapi.tiangolo.com/) and [Uvicorn](https://uvicorn.dev/). It is designed to be used as a starting point for small API services, standalone HTTP backends that bots and other clients call over the network instead of bundling heavy dependencies locally.

## Features

* FastAPI with automatic OpenAPI documentation at `/docs`.
* Bearer token authentication shared across all protected endpoints. A missing or wrong token gets `401 Unauthorized`, and tokens are compared in constant time.
* A `GET /health` endpoint for uptime monitoring, which the Docker image also uses as its health check.
* Configuration via environment variables using `pydantic-settings`. No values are hardcoded, and the service refuses to start with a placeholder or short secret.
* Structured JSON logging with a configurable log level. Every line is one JSON object, including uvicorn's access log.
* One version, set in `pyproject.toml`, which the health endpoint and the OpenAPI docs read from the installed package.
* `pyproject.toml` with the `hatchling` build backend, managed with [uv](https://docs.astral.sh/uv/) and locked in `uv.lock`.
* `Dockerfile` and `docker-compose.yml` for containerized deployment.
* A test suite with `pytest` covering health, auth rejection, and a template endpoint.
* Tests, linting, formatting, strict type checking, and a Docker build run in CI on every push to `main` and on every pull request through the shared [dev-standards](https://github.com/Lempki/dev-standards) workflow.

## Prerequisites

* [Docker](https://docs.docker.com/get-docker/) and Docker Compose for containerized setup.

Running without Docker requires Python 3.12 and [uv](https://docs.astral.sh/uv/). On Windows, install uv with `winget install --id astral-sh.uv`.

## Setup

The setup script prepares the project in a single run, and it is safe to run again at any time.

On Windows, double-click `setup.bat` or run it from a terminal:

```
setup.bat
```

On macOS or Linux, run the following commands:

```
chmod +x setup.sh
./setup.sh
```

The script asks before it installs anything, and it does the following:

1. It installs [uv](https://docs.astral.sh/uv/) when uv is missing. uv also provides Python 3.12 when the machine lacks it.
2. It offers to install Docker, and the tools that the Docker image includes for running outside Docker. It uses winget on Windows, Homebrew on macOS, and the system package manager on Linux.
3. It runs `uv sync`, which installs the package and its locked dependencies into `.venv`.
4. It copies `.env.template` to `.env` on the first run and fills `API_SECRET` with a random value.

A step that fails says what went wrong, why it matters, and what to do next, and the summary at the end lists it again.
The steps live in `scripts/bootstrap.py`, which needs only the Python standard library.

If you prefer to perform the setup manually, follow these steps:

```bash
uv sync
cp .env.template .env
# Edit .env and set API_SECRET and other values as needed.
uv run uvicorn api_template.main:app --reload
```

### Running

After setup has run once, the run script starts the API.
Double-click `run.bat` on Windows, or run `./run.sh` on macOS and Linux.
It builds and starts the API in Docker in the background, waits until its health check passes, and shows its status.
The container then starts again whenever Docker starts.

The script also takes an action, such as `run.bat stop` on Windows or `./run.sh stop` elsewhere:

| Action | What it does |
|---|---|
| `start` | Builds and starts everything in Docker and waits until it is ready. It is the default. |
| `stop` | Stops the containers. They stay stopped until the next start. |
| `status` | Shows whether each container runs and is healthy. |
| `logs` | Follows the logs. Press Ctrl+C to stop following. |
| `update` | Pulls the latest code, rebuilds on fresh base images, and restarts. |
| `local` | Runs the project in the terminal without Docker. Press Ctrl+C to stop it. |

When a service crashes right after it starts, the script shows the end of its log and stops it, so it does not restart over and over.
The `update` action needs a Git clone. In a downloaded release, it explains how to replace the files by hand instead.

### Docker

Alternatively, you can run the API as a Docker container.

1. Copy `.env.template` to `.env` and set `API_SECRET`.
2. Build and start the container:

   ```
   docker compose up --build
   ```

The API listens on port `8000` by default.
The service keeps no state, so the container needs no volume.

## Configuration

All configuration is read from environment variables or from a `.env` file in the project root.

| Variable | Required | Default | Description |
|---|---|---|---|
| `API_SECRET` | Yes | None | Shared bearer token of at least 16 characters. Callers must send this value in the `Authorization` header. Generate one with `python -c "import secrets; print(secrets.token_urlsafe(32))"`. |
| `LOG_LEVEL` | No | `INFO` | Log verbosity. Accepts `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. Every log line, including uvicorn's access log, is one JSON object. |

## Project structure

```
api-template/
├── src/api_template/
│   ├── main.py             # FastAPI application, lifespan, and route definitions.
│   ├── config.py           # This service's settings on top of ServiceSettings.
│   ├── service.py          # Shared settings, secret validation, and the version lookup.
│   ├── logging_config.py   # JSON logging for every logger, including uvicorn's.
│   ├── auth.py             # Bearer token dependency used to protect endpoints.
│   └── models.py           # Pydantic request and response models.
├── tests/
│   ├── test_api.py         # Tests for this service's own routes.
│   └── test_shared.py      # Tests for the shared auth, settings, logging, and version code.
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml          # Project metadata and dependencies.
├── uv.lock                 # Locked dependency versions.
├── ruff.toml               # Lint and format settings on top of the shared baseline.
├── .template-manifest.toml # Core files that derived APIs keep identical to this template.
├── setup.bat               # Windows setup script.
├── setup.sh                # macOS and Linux setup script.
├── scripts/bootstrap.py    # The steps that both setup scripts run.
├── scripts/run.py          # The actions that both run scripts take.
├── run.bat                 # Windows run script.
├── run.sh                  # macOS and Linux run script.
└── .env.template           # Template for environment variables.
```

## Creating a new API from this template

Use the GitHub template button to create a new repository based on this project. Then follow these steps to customize it:

1. **Rename the package.** In `pyproject.toml`, change the project `name` and the `packages` path under `[tool.hatch.build.targets.wheel]`. Rename the `src/api_template/` directory to match (e.g. `src/media_api/`). The source files import each other relatively, so only `tests/test_api.py` and the `CMD` line in `Dockerfile` name the package. Also set the new name as `package` under `[tool.dev-standards.template]` in `pyproject.toml` and as `known-first-party` in `ruff.toml`. Set `SERVICE` in `main.py` to the new project name, because the version is read from the installed project of that name. Then run `uv sync` so `uv.lock` records the new name.

2. **Add your dependencies.** Edit the `dependencies` list in `pyproject.toml`.

3. **Add configuration variables.** Extend the `Settings` class in `config.py` and document new variables in `.env.template`.

4. **Add startup and shutdown logic.** Use the `lifespan` context manager in `main.py` to load models, open connections, or perform any one-time initialisation.

5. **Add endpoints.** Define new routes in `main.py`. Use `dependencies=[Depends(require_auth)]` to protect them. Add request and response models to `models.py`.

6. **Remove the template endpoint.** Delete the `/template/echo` route and the `TemplateRequest`/`TemplateResponse` models once you have your own routes in place.

7. **Update the `docker-compose.yml` port.** Change the host side of `8000:8000` to the port assigned to your service, such as `8001:8000`. The container itself keeps listening on port 8000.

8. **Write tests.** Add test functions to `tests/test_api.py`. Leave `tests/test_shared.py` unchanged, because it is a core file.

## Running tests

```bash
uv run pytest
uv run mypy src
```

Run every lint and format check with `uvx pre-commit run --all-files`, or install the hooks once with `uvx pre-commit install` so they run on each commit.
The coding, prose, and commit conventions are documented in [dev-standards](https://github.com/Lempki/dev-standards).

## Calling protected endpoints

All endpoints except `/health` require a bearer token in the `Authorization` header.
A request without the header or with a wrong token gets `401 Unauthorized` with a `WWW-Authenticate: Bearer` header:

```http
POST /template/echo HTTP/1.1
Authorization: Bearer your-secret-here
Content-Type: application/json

{"text": "hello"}
```

A Python client calling this API can use `httpx.AsyncClient` with the token set as a default header:

```python
import httpx

client = httpx.AsyncClient(
    base_url="http://localhost:8000",
    headers={"Authorization": "Bearer your-secret-here"},
)
```

## Related services

The following APIs were built from this template and can serve as fuller implementation examples.

| Service | Description |
|---|---|
| [api-media](https://github.com/Lempki/api-media) | Resolves YouTube, SoundCloud, and Spotify track metadata and stream URLs. |
| [api-scraper](https://github.com/Lempki/api-scraper) | Scrapes structured data from external websites. |
| [api-scheduler](https://github.com/Lempki/api-scheduler) | Schedules persistent reminders delivered via Discord webhooks. |
| [api-morshu](https://github.com/Lempki/api-morshu) | Generates Morshu TTS audio and video from text. |

## License

This project is licensed under the [MIT License](LICENSE).
You may use, change, and share it, as long as every copy keeps the copyright notice and the license text.
