# discord-api-template

A FastAPI template for the small HTTP services that the Discord bots call.
Services such as discord-api-media and discord-api-scheduler are created from it.
The shared conventions live in [discord-dev-standards](https://github.com/Lempki/discord-dev-standards), and its README is the rulebook for code, prose, and commits.

## Commands

* `uv sync` installs the package and its locked dependencies into `.venv`.
* `uv run uvicorn api_template.main:app --reload` starts the API on port 8000. It reads its settings from `.env`.
* `uv run pytest` runs the tests.
* `uvx pre-commit run --all-files` runs every lint and format hook.

## Layout

* `src/api_template/main.py` defines the app, the lifespan, and the routes.
* `src/api_template/config.py` adds this service's settings to `ServiceSettings`.
* `src/api_template/service.py` holds `ServiceSettings`, which validates the shared secret, and `service_version()`, which reads the version from pyproject.toml.
* `src/api_template/logging_config.py` turns every log record, including uvicorn's, into one JSON line.
* `src/api_template/auth.py` holds the bearer token dependency that protects every route except `/health`.
* `src/api_template/models.py` holds the request and response models.
* `tests/test_shared.py` tests the shared modules and is a core file. `tests/test_api.py` tests this service's own routes.

## Template rules

* `.template-manifest.toml` lists the core files that every derived API keeps identical to this template.
* Change a core file here first. Derived APIs then pick it up with `dev-standards template-check --template <path-to-discord-api-template> --apply`.
* Service-specific behavior belongs in files outside the manifest, such as `main.py`, `config.py`, and `models.py`.
* Keep the version only in pyproject.toml, and keep `SERVICE` in main.py equal to the project name there.
* `uv run mypy src` must pass in strict mode, because CI runs it.
