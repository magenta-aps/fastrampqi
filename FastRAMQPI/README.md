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
from typing import Any

from fastapi import APIRouter
from fastapi import FastAPI
from gql.client import AsyncClientSession
from pydantic import BaseSettings
from pydantic import Field
from ramqp.depends import Context
from ramqp.depends import RateLimit
from ramqp.mo import MORouter
from ramqp.mo import PayloadUUID

from fastramqpi import depends
from fastramqpi.config import Settings as FastRAMQPISettings
from fastramqpi.main import FastRAMQPI


class Settings(BaseSettings):
    class Config:
        frozen = True
        env_nested_delimiter = "__"

    fastramqpi: FastRAMQPISettings = Field(
        default_factory=FastRAMQPISettings, description="FastRAMQPI settings"
    )


fastapi_router = APIRouter()
amqp_router = MORouter()


@amqp_router.register("engagement")
async def listen_to_engagements(
        context: Context,
        graphql_session: depends.LegacyGraphQLSession,
        uuid: PayloadUUID,
        _: RateLimit
) -> None:
    print(uuid)


def create_fastramqpi(**kwargs: Any) -> FastRAMQPI:
    settings = Settings(**kwargs)
    fastramqpi = FastRAMQPI(
        application_name="os2mo-example-integration",
        settings=settings.fastramqpi,
        graphql_version=20,
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


## Autogenerated GraphQL Client
FastRAMQPI exposes an
[authenticated httpx client](https://docs.authlib.org/en/latest/client/api.html#authlib.integrations.httpx_client.AsyncOAuth2Client)
through the dependency injection system. While it is possible to call the OS2mo
API directly through it, the recommended approach is to define a properly-typed
GraphQL client in the integration and configure it to make calls through the
authenticated client. Instead of manually implementing such client, we strongly
recommend to use the
[**Ariadne Code Generator**](https://github.com/mirumee/ariadne-codegen), which
generates an integration-specific client based on the general OS2mo GraphQL
schema and the exact queries and mutations the integration requires.

To integrate such client, first add and configure the codegen:
```toml
# pyproject.toml

[tool.poetry.dependencies]
ariadne-codegen = {extras = ["subscriptions"], version = "^0.7.1"}

[tool.ariadne-codegen]
# Ideally, the GraphQL client is generated as part of the build process and
# never committed to git. Unfortunately, most of our tools and CI analyses the
# project directly as it is in Git. In the future - when the CI templates
# operate on the built container image - only the definition of the schema and
# queries should be checked in.
#
# The default package name is `graphql_client`. Make it more obvious that the
# files are not to be modified manually.
target_package_name = "autogenerated_graphql_client"
target_package_path = "my_integration/"
client_name = "GraphQLClient"
schema_path = "schema.graphql"  # curl -O http://localhost:5000/graphql/v8/schema.graphql
queries_path = "queries.graphql"
plugins = [
    # Return values directly when only a single top field is requested
    "ariadne_codegen.contrib.shorter_results.ShorterResultsPlugin",
]
[tool.ariadne-codegen.scalars.DateTime]
type = "datetime.datetime"
[tool.ariadne-codegen.scalars.UUID]
type = "uuid.UUID"
```
Where you replace `"my_integration/"` with the path to your integration.

Grab OS2mo's GraphQL schema:
```bash
curl -O http://localhost:5000/graphql/v20/schema.graphql
```
Define your queries:
```gql
# queries.graphql

# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0

query Version {
  version {
    mo_version
    mo_hash
  }
}
```
Generate the client - you may have to activate some virtual environment:
```bash
ariadne-codegen
```
The client class is passed to FastRAMQPI on startup as shown below. This will
ensure it is automatically opened and closed and configured with
authentication. **NOTE: remember to update the `graphql_version` when you
generate against a new schema version**.

```python
# app.py
from autogenerated_graphql_client import GraphQLClient


def create_app(**kwargs: Any) -> FastAPI:
    fastramqpi = FastRAMQPI(
        ...,
        graphql_version=20,
        graphql_client_cls=GraphQLClient,
    )
```
The FastRAMQPI framework cannot define the annotated type for the GraphQL client
since its methods depend on the specific queries required by the integration.
Therefore, each implementing integration needs to define their own:
```python
# depends.py
from typing import Annotated

from fastapi import Depends
from ramqp.depends import from_context

from my_integration.autogenerated_graphql_client import GraphQLClient as _GraphQLClient

GraphQLClient = Annotated[_GraphQLClient, Depends(from_context("graphql_client"))]
```
Finally, we can define our AMQP handler to use the GraphQL client:
```python
# events.py
from . import depends


@router.register("*")
async def handler(mo: depends.GraphQLClient) -> None:
    version = await mo.version()
    print(version)
```

To get REUSE working, you might consider adding the following to `.reuse/dep5`:
```text
Files: my_integration/autogenerated_graphql_client/*
Copyright: Magenta ApS <https://magenta.dk>
License: MPL-2.0
```


## Integration Testing
The goal of integration testing in our context is to minimise the amount of
mocking and patching by testing the integration's behavior against a running
OS2mo instance in a way that resembles a production environment as much as
possible. To this end, the integration is configured for testing through its
public interface -- environment variables -- in `.gitlab-ci.yml` wherever
possible. The flow of each test follows the well-known "Arrange, Act and
Assert" pattern, but with a sleight modification to avoid hooking into either
OS2mo or the integration itself, and endure the nature of eventual consistency
that is unavoidable with an event-based system.

To get started, add OS2mo's [GitLab CI template](https://git.magenta.dk/rammearkitektur/os2mo/-/blob/master/gitlab-ci-templates/integration-test-meta.v1.yml)
to `.gitlab-ci.yml`:
```yaml
include:
  - project: rammearkitektur/os2mo
    file:
      - gitlab-ci-templates/integration-test-meta.v1.yml

...

Test:
  variables:
    PYTEST_ADDOPTS: "-m 'not integration_test'"

Integration-test:
  extends:
    - .integration-test:mo
  variables:
    MY_INTEGRATION__FOO: "true"
```

The `Integration-test` CI job starts a full OS2mo stack, including all
necessary services, and then runs all tests marked with `integration_test`.
[Auto-used fixtures](fastramqpi/pytest_plugin.py) automatically ensure test
isolation in OS2mo's database, increase the AMQP messaging interval, and
configure `respx` appropriately. By default, the `Test` job runs all tests in
the project, including both unit- and integration-tests. We overwrite the
`Test` CI job to exclude integration tests -- the `Integration-test` job
already only runs integration tests by default.

Moving on, some boilerplate needs to be copied since a few types cannot be
known a priori:
```python
# tests/integration/conftest.py
import pytest
from collections.abc import AsyncIterator
from collections.abc import Iterator
from fastapi.testclient import TestClient
from gql.client import AsyncClientSession
from my_integration.app import create_app


@pytest.fixture
def test_client() -> Iterator[TestClient]:
    """Create ASGI test client with associated lifecycles."""
    app = create_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def graphql_client(test_client: TestClient) -> AsyncClientSession:
    """Authenticated GraphQL codegen client for OS2mo."""
    return test_client.app_state["context"]["graphql_client"]
```
The `test_client` fixture refers to a running instance of the integration, and
`graphql_client` to the integration's pre-authenticated instance of its
[autogenerated GraphQL client](#autogenerated-graphql-client).

A sample integration test could be as follows:

```python
# tests/integration/test_my_integration.py
import pytest
from fastapi.testclient import TestClient
from fastramqpi.pytest_util import retry
from more_itertools import one

from my_integration.autogenerated_graphql_client import GraphQLClient


@pytest.mark.integration_test
async def test_create_person(
        test_client: TestClient,
        graphql_client: GraphQLClient,
) -> None:
    # Precondition: The person does not already exist.
    # The auto-use fixtures should automatically ensure test isolation, but
    # sometimes, especially during local development, we might be a little too
    # fast on the ^C^C^C^C^C so pytest doesn't get a chance to clean up.
    cpr_number = "1234567890"
    employee = await graphql_client._testing__get_employee(cpr_number)
    assert employee.objects == []

    # The integration needs to be triggered to create the employee. How this is
    # done depends on the integration. We assume a /trigger/ endpoint here:
    test_client.post("/trigger")

    @retry()
    async def verify() -> None:
        employees = await graphql_client._testing__get_employee(cpr_number)
        employee_states = one(employees.objects)
        employee = one(employee_states.objects)
        assert employee.cpr_number == cpr_number
        assert employee.given_name == "Alice"
    
    await verify()
```
Through the use of the `test_client` fixture, the test begins by starting the
integration, including initialising any associated lifecyles such as AMQP
connections. We sanity-check, to ensure the test isn't trivially passing, and
trigger the integration. Due to the nature of AMQP, we don't know how long the
integration will need to reconcile the state of OS2mo or an external system.
Therefore, all asserts which depend on eventual consistent state, are wrapped
in a function with `@retry` from FastRAMQPI's `pytest_util`. This allows the
assertions to fail and be retried up to 30 seconds, before the test fails.

To keep tests clear and concise, all GraphQL queries, which are required to
arrange and assert in the test, are added to the [autogenerated GraphQL client](#autogenerated-graphql-client),
using a `_testing__` prefix by convention:
```graphql
# queries.graphql
query _Testing_GetEmployee($cpr_number: CPR!) {
  employees(filter: {cpr_numbers: [$cpr_number]}) {
    objects {
      objects {
        cpr_number
        given_name
      }
    }
  }
}
```

### Overriding OS2mo-init
It is possible to specific a custom [OS2mo-init](https://git.magenta.dk/rammearkitektur/os2mo-init)
configuration by setting the `OS2MO_INIT_CONFIG` variable at the top of the
project's `.gitlab-ci.yml` and declaring a `init.config.yml`:
```yaml
# .gitlab-ci.yml
variables:
  OS2MO_INIT_CONFIG: "/builds/$CI_PROJECT_PATH/init.config.yml"

# init.config.yml
facets:
  org_unit_address_type: {}
  manager_address_type: {}
  address_property: {}
  engagement_job_function: {}
  org_unit_type: {}
  engagement_type:
    qa_engineer:
      title: "Software Integration Tester"
      scope: "TEXT"
  association_type: {}
  role_type: {}
  leave_type: {}
  manager_type: {}
  responsibility: {}
  manager_level: {}
  visibility: {}
  time_planning: {}
  org_unit_level: {}
  primary_type: {}
  org_unit_hierarchy: {}
  kle_number: {}
  kle_aspect: {}

it_systems:
  FOOBAR: "The Foo Bar"
```


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