<!--
SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
SPDX-License-Identifier: MPL-2.0
-->

# FastRAMQPI

FastRAMQPI is an opinionated library for FastAPI and RAMQP.

It is implemented as a thin wrapper around `FastAPI` and `RAMQP`.
It is very MO specific.

## Usage

```python
from pydantic import BaseSettings
from fastramqpi import FastRAMQPI
from fastramqpi import FastRAMQPISettings


class Settings(BaseSettings):
    class Config:
        frozen = True
        env_nested_delimiter = "__"

    fastramqpi: FastRAMQPISettings = Field(
        default_factory=FastRAMQPISettings,
        description="FastRAMQPI settings"
    )

    # All your program settings hereunder...


fastapi_router = APIRouter()

@fastapi_router.post("/trigger/all")
async def update_all(request: Request) -> dict[str, str]:
    context: dict[str, Any] = request.app.state.context
    graphql_session = context["grapqh_session"]
    program_settings = context["user_context"]["settings"]
    ...
    return {"status": "OK"}


amqp_router = MORouter()

@amqp_router.register("*.*.*")
async def listen_to_all(context: dict, payload: PayloadType) -> None:
    graphql_session = context["grapqh_session"]
    program_settings = context["user_context"]["settings"]
    ...


def create_fastramqpi(**kwargs: Any) -> FastRAMQPI:
    settings = Settings(**kwargs)
    fastramqpi = FastRAMQPI(
        application_name="orggatekeeper", settings=settings.fastramqpi
    )
    fastramqpi.add_context(settings=settings)

    # Add our AMQP router(s)
    amqpsystem = fastramqpi.get_amqpsystem()
    amqpsystem.router.registry.update(amqp_router.registry)

    # Add our FastAPI router(s)
    app = fastramqpi.get_app()
    app.include_router(fastapi_router)

    return fastramqpi


def create_app(**kwargs: Any) -> FastAPI:
    fastramqpi = create_fastramqpi(**kwargs)
    return fastramqpi.get_app()
```

### Metrics
FastRAMQPI Metrics are exported via `prometheus/client_python` on the FastAPI's `/metrics`.

## Development

### Prerequisites

- [Poetry](https://github.com/python-poetry/poetry)

### Getting Started

1. Clone the repository:
```
git clone git@git.magenta.dk:rammearkitektur/FastRAMQPI.git
```

2. Install all dependencies:
```
poetry install
```

3. Set up pre-commit:
```
poetry run pre-commit install
```

### Running the tests

You use `poetry` and `pytest` to run the tests:

`poetry run pytest`

You can also run specific files

`poetry run pytest tests/<test_folder>/<test_file.py>`

and even use filtering with `-k`

`poetry run pytest -k "Manager"`

You can use the flags `-vx` where `v` prints the test & `x` makes the test stop if any tests fails (Verbose, X-fail)

## Authors

Magenta ApS <https://magenta.dk>

## License

This project uses: [MPL-2.0](LICENSES/MPL-2.0.txt)

This project uses [REUSE](https://reuse.software) for licensing.
All licenses can be found in the [LICENSES folder](LICENSES/) of the project.
