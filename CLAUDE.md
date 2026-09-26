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
* `src/api_template/config.py` reads settings from the environment with pydantic-settings.
* `src/api_template/auth.py` holds the bearer token dependency that protects every route except `/health`.
* `src/api_template/models.py` holds the request and response models.

## Template rules

* `.template-manifest.toml` lists the core files that every derived API keeps identical to this template.
* Change a core file here first. Derived APIs then pick it up with `dev-standards template-check --apply`.
* Service-specific behavior belongs in files outside the manifest, such as `main.py`, `config.py`, and `models.py`.
